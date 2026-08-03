from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator


class SubstanceInput(BaseModel):
    """Maps to usdm4.api.substance.Substance (+ Strength) inside an
    Ingredient on an AdministrableProduct.

    ``strength`` is a human-readable string: "10 mg" (numerator only),
    "50 mg/5 mL" or "50 mg/mL" (numerator/denominator). Unparseable
    strengths are dropped with a warning.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    strength: Optional[str] = None


class ProductInput(BaseModel):
    """Maps to usdm4.api.administrable_product.AdministrableProduct.

    ``dose_form`` (e.g. "Tablet", "Injection") and
    ``product_designation`` ("IMP" / "NIMP") resolve against CDISC CT;
    both are required on the API model, so unresolvable or empty input
    degrades to warned defaults (Unknown dose form, IMP). Each substance
    becomes an Ingredient with the Active Ingredient role — richer
    ingredient roles and pharmacologic class codes are out of scope for
    assembler input.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    dose_form: str = ""
    product_designation: str = ""
    substances: list[SubstanceInput] = []


class AdministrationDurationInput(BaseModel):
    """Maps to usdm4.api.duration.Duration on an Administration.

    ``quantity`` is a human-readable value+unit string (e.g. "1 min",
    "6 weeks"); the assembler parses it into a USDM ``Quantity`` where the
    unit resolves against CDISC CT, falling back to carrying the raw string
    on ``Duration.text`` when it does not.
    """

    model_config = ConfigDict(strict=False)

    description: str = ""
    will_vary: bool = False
    will_vary_reason: str = ""
    quantity: Optional[str] = None


class AdministrationInput(BaseModel):
    """Maps to usdm4.api.administration.Administration.

    ``dose`` is a human-readable value+unit string (e.g. "10 mg",
    "2.5 mg/kg") parsed to a ``Quantity`` at assembly time, with the raw
    text preserved on the administration description when it does not
    parse; ``route`` and ``frequency`` are encoded via the C66729 / C71113
    codelists. ``name`` is optional — the assembler generates one when
    absent.
    """

    model_config = ConfigDict(strict=False)

    name: str = ""
    label: str = ""
    description: str = ""
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[AdministrationDurationInput] = None
    # Label-based reference into ``StudyDesignInput.products``; resolved to
    # ``administrableProductId`` at assembly time.
    product_name: str = ""


class InterventionInput(BaseModel):
    """Maps to usdm4.api.study_intervention.StudyIntervention + Administration.

    Human-readable strings in, CDISC codes out: the assembler is responsible
    for looking up codes via cdisc_code(...) / encoder.* methods.

    Administrations can be supplied two ways:

    - ``administrations``: the full multi-administration list; or
    - flat ``dose`` / ``route`` / ``frequency``: back-compat sugar that the
      assembler collapses into a single ``Administration``.

    Supplying both is rejected — the flat fields would be ambiguous
    (a fourth administration? an override of the first?).
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    type: str = ""
    role: str = ""
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    administrations: list[AdministrationInput] = []

    @model_validator(mode="after")
    def _check_flat_vs_administrations(self) -> "InterventionInput":
        if self.administrations and (self.dose or self.route or self.frequency):
            raise ValueError(
                f"intervention {self.name!r} supplies both flat "
                f"dose/route/frequency and an administrations list; "
                f"use one or the other"
            )
        return self


class ArmInput(BaseModel):
    """Maps to usdm4.api.study_arm.StudyArm.

    ``intervention_names`` holds label-based references into the sibling
    ``StudyDesignInput.interventions`` list; IDs are a post-assembly concern.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    type: str = ""
    intervention_names: list[str] = []
    planned_enrollment: Optional[int] = None


class ElementInput(BaseModel):
    """Maps to usdm4.api.study_element.StudyElement.

    Elements typically carry load-bearing regimen information (dose schedules
    that vary across cycles, combination vs. monotherapy, de-escalation
    doses). Cells reference elements by name via ``CellInput.elements``; the
    ``StudyDesignInput`` validator enforces that every cell reference
    resolves to a declared element.
    """

    model_config = ConfigDict(strict=False)

    name: str
    label: str = ""
    description: str = ""
    intervention_names: list[str] = []


class CellInput(BaseModel):
    """Maps to usdm4.api.study_cell.StudyCell.

    ``arm`` and ``epoch`` are label-based references (case-insensitive match,
    same convention as ``_add_epochs``). If ``StudyDesignInput.cells`` is
    empty the assembler derives a default arm x epoch grid.
    """

    model_config = ConfigDict(strict=False)

    arm: str
    epoch: str
    elements: list[str] = []


class StudyDesignInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    rationale: str = ""
    trial_phase: str = ""
    intervention_model: str = ""
    arms: list[ArmInput] = []
    interventions: list[InterventionInput] = []
    cells: list[CellInput] = []
    elements: list[ElementInput] = []
    products: list[ProductInput] = []

    @model_validator(mode="after")
    def _check_administration_product_references(self) -> "StudyDesignInput":
        """Every ``AdministrationInput.product_name`` must resolve to a
        declared ``ProductInput.name`` on this model."""
        product_names = {p.name for p in self.products}
        for intervention in self.interventions:
            for admin in intervention.administrations:
                if admin.product_name and admin.product_name not in product_names:
                    declared = sorted(product_names) if product_names else "(none)"
                    raise ValueError(
                        f"intervention {intervention.name!r} administration "
                        f"references undeclared product {admin.product_name!r}; "
                        f"declared products: {declared}"
                    )
        return self

    @model_validator(mode="after")
    def _check_arm_intervention_references(self) -> "StudyDesignInput":
        """Every ``ArmInput.intervention_names`` entry must resolve to a
        declared ``InterventionInput.name`` on this model.

        Same-model sibling of the cell -> element check below; the assembler
        additionally guards the reference at build time for direct dict use.
        """
        intervention_names = {i.name for i in self.interventions}
        for arm in self.arms:
            for ref in arm.intervention_names:
                if ref not in intervention_names:
                    declared = (
                        sorted(intervention_names) if intervention_names else "(none)"
                    )
                    raise ValueError(
                        f"arm {arm.name!r} references undeclared intervention "
                        f"{ref!r}; declared interventions: {declared}"
                    )
        return self

    @model_validator(mode="after")
    def _check_cell_element_references(self) -> "StudyDesignInput":
        """Every ``CellInput.elements`` entry must resolve to an
        ``ElementInput.name`` declared on this model.

        Captures the Step 5 invariant that elements carry load-bearing design
        information and cannot be synthesised from cells: when any cell lists
        element names, those names must refer to explicitly declared elements.
        """
        element_names = {e.name for e in self.elements}
        for cell in self.cells:
            for ref in cell.elements:
                if ref not in element_names:
                    declared = sorted(element_names) if element_names else "(none)"
                    raise ValueError(
                        f"cell ({cell.arm!r}, {cell.epoch!r}) references "
                        f"undeclared element {ref!r}; declared elements: {declared}"
                    )
        return self
