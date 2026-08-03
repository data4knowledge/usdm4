from pydantic import BaseModel, ConfigDict, model_validator


class EndpointInput(BaseModel):
    """Maps to usdm4.api.endpoint.Endpoint (a SyntaxTemplate).

    ``level`` is a human-readable label (Primary / Secondary / Exploratory,
    or the full CDISC decode e.g. "Primary Endpoint"); the assembler encodes
    it to a CDISC Code (codelist C188726). ``name`` is optional — the
    assembler generates one when absent — but an endpoint that an estimand
    references via ``EstimandInput.endpoint_name`` must declare its name
    explicitly so the reference can resolve.
    """

    model_config = ConfigDict(strict=False)

    name: str = ""
    label: str = ""
    description: str = ""
    text: str
    purpose: str = ""
    level: str = ""


class ObjectiveInput(BaseModel):
    """Maps to usdm4.api.objective.Objective (a SyntaxTemplate).

    ``level`` is a human-readable label (Primary / Secondary / Exploratory,
    or the full CDISC decode e.g. "Trial Primary Objective"); the assembler
    encodes it to a CDISC Code (codelist C188725). Endpoints nest under
    their objective, mirroring the API model.
    """

    model_config = ConfigDict(strict=False)

    name: str = ""
    label: str = ""
    description: str = ""
    text: str
    level: str = ""
    endpoints: list[EndpointInput] = []


class IntercurrentEventInput(BaseModel):
    """Maps to usdm4.api.intercurrent_event.IntercurrentEvent.

    ``strategy`` is free text on the API model (ICH E9(R1) strategies:
    treatment policy, hypothetical, composite, while on treatment,
    principal stratum) — no encoding is applied.
    """

    model_config = ConfigDict(strict=False)

    name: str = ""
    label: str = ""
    description: str = ""
    text: str
    strategy: str = ""


class EstimandInput(BaseModel):
    """Maps to usdm4.api.estimand.Estimand + AnalysisPopulation.

    References are name-based and resolved late, mirroring
    ``CohortInput.arm_names``:

    - ``endpoint_name`` → a named ``EndpointInput`` declared on this
      ``ObjectivesInput`` (validated here, both live on the same model) →
      ``Estimand.variableOfInterestId``.
    - ``treatment_names`` → ``StudyDesignInput.interventions[*].name``
      (validated at the ``AssemblerInput`` level where both are visible) →
      ``Estimand.interventionIds``.
    - ``population_subset_names`` → cohort names on ``PopulationInput`` (or
      the population label itself) → ``AnalysisPopulation.subsetOfIds``.
      When empty the analysis population subsets the whole study population.

    ``population_text`` is the analysis population description (M11 estimand
    table "Population" row); one ``AnalysisPopulation`` is created per
    estimand. ``summary_measure`` is the population-level summary.
    """

    model_config = ConfigDict(strict=False)

    name: str = ""
    label: str = ""
    description: str = ""
    summary_measure: str
    population_text: str = ""
    population_subset_names: list[str] = []
    treatment_names: list[str] = []
    endpoint_name: str
    intercurrent_events: list[IntercurrentEventInput] = []


class ObjectivesInput(BaseModel):
    model_config = ConfigDict(strict=False)

    objectives: list[ObjectiveInput] = []
    estimands: list[EstimandInput] = []

    @model_validator(mode="after")
    def _check_estimand_endpoint_references(self) -> "ObjectivesInput":
        """Every ``estimand.endpoint_name`` must resolve to a *named*
        endpoint declared on an objective of this model.

        Unnamed endpoints are legal (the assembler generates names) but
        cannot be referenced — the reference is checked against explicit
        input names only, before any generation happens.
        """
        endpoint_names = {
            e.name for o in self.objectives for e in o.endpoints if e.name
        }
        for estimand in self.estimands:
            if estimand.endpoint_name not in endpoint_names:
                declared = sorted(endpoint_names) if endpoint_names else "(none)"
                raise ValueError(
                    f"estimand {estimand.name or estimand.summary_measure!r} "
                    f"references undeclared endpoint {estimand.endpoint_name!r}; "
                    f"declared named endpoints: {declared}"
                )
        return self
