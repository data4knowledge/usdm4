import copy
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.api.address import Address
from usdm4.api.organization import Organization
from usdm4.api.identifier import StudyIdentifier, SIT_EXT_URL, ExtensionAttribute
from usdm4.api.study_title import StudyTitle
from usdm4.api.study_role import StudyRole
from usdm4.api.code import Code
from usdm4.api.extension import BaseCode
from usdm4.api.assigned_person import AssignedPerson
from usdm4.api.person_name import PersonName
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation


class IdentificationAssembler(BaseAssembler):
    """
    Assembler for processing study identification information including titles, identifiers, and organizations.

    This assembler handles the creation of study titles, study identifiers, and associated organizations
    based on input data. It supports both standard predefined organizations (like CT.GOV, EMA, FDA)
    and custom non-standard organizations.

    Attributes:
        MODULE (str): Module path for error reporting
        TITLE_TYPES (list): Supported study title types
        TITLE_CODES (dict): Mapping of title types to CDISC codes
        ORG_CODES (dict): Mapping of organization types to CDISC codes
        STANDARD_ORGS (dict): Predefined standard organizations with their details
    """

    MODULE = "usdm4.assembler.identification_assembler.IdentificationAssembler"

    TITLE_TYPES = [
        "brief",
        "official",
        "public",
        "scientific",
        "acronym",
    ]

    ROLE_CODES = {
        "co-sponsor": {"code": "C215669", "decode": "Co-Sponsor"},
        "manufacturer": {"code": "C25392", "decode": "Manufacturer"},
        "investigator": {"code": "C25936", "decode": "Investigator"},
        "pharmacovigilance": {"code": "C215673", "decode": "Pharmacovigilance"},
        "project maanger": {"code": "C51851", "decode": "Project Manager"},
        "local sponsor": {"code": "C215670", "decode": "Local Sponsor"},
        "laboratory": {"code": "C37984", "decode": "Laboratory"},
        "study subject": {"code": "C41189", "decode": "Study Subject"},
        "medical expert": {"code": "C51876", "decode": "Medical Expert"},
        "statistician": {"code": "C51877", "decode": "Statistician"},
        "idmc": {"code": "C142578", "decode": "Independent Data Monitoring Committee"},
        "care provider": {"code": "C17445", "decode": "Care Provider"},
        "principal investigator": {
            "code": "C19924",
            "decode": "Principal investigator ",
        },
        "outcomes assessor": {"code": "C207599", "decode": "Outcomes Assessor      "},
        "dec": {"code": "C215671", "decode": "Dose Escalation Committee"},
        "clinical trial physician": {
            "code": "C215672",
            "decode": "Clinical Trial Physician",
        },
        "sponsor": {"code": "C70793", "decode": "Sponsor"},
        "adjudication Committee": {
            "code": "C78726",
            "decode": "Adjudication Committee",
        },
        "study site": {"code": "C80403", "decode": "Study Site"},
        "dsmb": {"code": "C142489", "decode": "Data Safety Monitoring Board"},
        "regulatory agency": {"code": "C188863", "decode": "Regulatory Agency"},
        "contract research": {"code": "C215662", "decode": "Contract Research"},
    }

    ROLE_ORGS = {
        "co_sponsor": {
            "type": "pharma",
            "role": "co-sponsor",
            "description": "The co-sponsor organization",
            "label": "",
            "identifier": "Not known",
            "identifierScheme": "Not known",
            "legalAddress": {},
        },
        "local_sponsor": {
            "type": "pharma",
            "role": "local sponsor",
            "description": "The local sponsor organization",
            "label": "",
            "identifier": "Not known",
            "identifierScheme": "Not known",
            "legalAddress": {},
        },
        "device_manufacturer": {
            "type": "medical_device",
            "role": "manufacturer",
            "description": "The medical device manufacturer",
            "label": "",
            "identifier": "Not known",
            "identifierScheme": "Not known",
            "legalAddress": {},
        },
    }

    TITLE_CODES = {
        "brief": {"code": "C207615", "decode": "Brief Study Title"},
        "official": {"code": "C207616", "decode": "Official Study Title"},
        "public": {"code": "C207617", "decode": "Public Study Title"},
        "scientific": {"code": "C207618", "decode": "Scientific Study Title"},
        "acronym": {"code": "C207646", "decode": "Study Acronym"},
    }

    ORG_CODES = {
        "registry": {"code": "C93453", "decode": "Clinical Study Registry"},
        "regulator": {"code": "C188863", "decode": "Regulatory Agency"},
        "healthcare": {"code": "C21541", "decode": "Healthcare Facility"},
        "pharma": {"code": "C54149", "decode": "Pharmaceutical Company"},
        "lab": {"code": "C37984", "decode": "Laboratory"},
        "cro": {"code": "C54148", "decode": "Contract Research Organization"},
        "gov": {"code": "C199144", "decode": "Government Institute"},
        "academic": {"code": "C18240", "decode": "Academic Institution"},
        "medical_device": {"code": "C215661", "decode": "Medical Device Company"},
    }

    IDENTIFIER_CODES = {
        "nct": {"code": "C172240", "decode": "Clinicaltrials.gov Identifier"},
        "jrct": {
            "code": "C218687",
            "decode": "Japan Registry for Clinical Trials Number",
        },
        "nmpa": {"code": "C218688", "decode": "NMPA IND Number"},
        "other": {
            "code": "C218690",
            "decode": "Other Regulatory or Clinical Trial Identifier",
        },
        "who": {"code": "C218689", "decode": "WHO/UTN Number"},
        "ema": {"code": "C218684", "decode": "EU Clinical Trial Register Number"},
        "fda-ind": {
            "code": "C218685",
            "decode": "US FDA Investigational New Drug Application Number",
        },
        "fda-ide": {
            "code": "C218686",
            "decode": "US FDA Investigational Device Exemption Application Number",
        },
    }

    STANDARD_ORGS = {
        "nct": {
            "type": "registry",
            "role": None,
            "name": "CT.GOV",
            "label": "ClinicalTrials.gov",
            "description": "The US clinical trials registry",
            "identifier": "ClinicalTrials.gov",
            "identifierScheme": "National Institute of Health, US Government",
            "legalAddress": {
                "lines": ["National Library of Medicine", "8600 Rockville Pike"],
                "city": "Bethesda",
                "district": "",
                "state": "MD",
                "postalCode": "20894",
                "country": "USA",
            },
        },
        "ema": {
            "type": "regulator",
            "role": "regulatory agency",
            "name": "EMA",
            "label": "European Medicines Agency",
            "description": "The European medicines regulator",
            "identifier": "EMA",
            "identifierScheme": "European Union",
            "legalAddress": {
                "lines": ["Domenico Scarlattilaan 6"],
                "city": "Amsterdam",
                "district": "",
                "state": "",
                "postalCode": "1083 HS",
                "country": "NL",
            },
        },
        "fda-ind": {
            "type": "regulator",
            "role": "regulatory agency",
            "name": "FDA",
            "label": "Food and Drug Administration",
            "identifier": "FDA",
            "description": "The US medicines regulator",
            "identifierScheme": "Health and Human Services, US Government",
            "legalAddress": {
                "lines": ["10903 New Hampshire Ave"],
                "city": "Silver Spring",
                "district": "",
                "state": "MD",
                "postalCode": "20903",
                "country": "USA",
            },
        },
        "fda-ide": {
            "type": "regulator",
            "role": "regulatory agency",
            "name": "FDA",
            "label": "Food and Drug Administration",
            "identifier": "FDA",
            "description": "The US medicines regulator",
            "identifierScheme": "Health and Human Services, US Government",
            "legalAddress": {
                "lines": ["10903 New Hampshire Ave"],
                "city": "Silver Spring",
                "district": "",
                "state": "MD",
                "postalCode": "20903",
                "country": "USA",
            },
        },
        "jrct": {
            "type": "registry",
            "role": None,
            "name": "jRCT",
            "label": "Japan Registry of Clinical Trials",
            "identifier": "JRCT",
            "description": "The Japanese clinical trial registry",
            "identifierScheme": "Ministry of Health, Labour and Welfare of Japan",
            "legalAddress": {
                "lines": ["1-2-2 Kasumigaseki"],
                "city": "Tokyo",
                "district": "Chiyoda",
                "state": "",
                "postalCode": "",
                "country": "JPN",
            },
        },
        "nmpa": {
            "type": "regulator",
            "role": "regulatory agency",
            "name": "NMPA",
            "label": "National Medical Products Administration",
            "identifier": "NMPA",
            "description": "The Chinese medicines regulator",
            "identifierScheme": "People's Republic of China Government",
            "legalAddress": {
                "lines": ["No. 1 Beiluyuan", "Zhanlan Road"],
                "city": "Beijing",
                "district": "Xicheng District",
                "state": "",
                "postalCode": "100037",
                "country": "CHN",
            },
        },
        "who": {
            "type": "registry",
            "role": None,
            "name": "WHO UTN",
            "label": "WHO Registry of Clinical Trials",
            "identifier": "WHO UTN",
            "description": "The WHP clinical trial registry",
            "identifierScheme": "United Nations",
            "legalAddress": {
                "lines": ["20 Avenue Appia"],
                "city": "Geneva",
                "district": "27",
                "state": "",
                "postalCode": "CH-1211",
                "country": "CHE",
            },
        },
    }

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the IdentificationAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self.clear()

    def clear(self):
        self._titles = []
        self._organizations = []
        self._identifiers = []
        self._roles = []
        self._study_name = ""
        self._sponsor_signatory = None
        self._compound_names = None
        self._compound_codes = None
        self._medical_expert_contact_details_location = None

    def execute(self, data: dict) -> None:
        """
        Process study identification data to create titles, identifiers, and organizations.

        This method processes the input data dictionary to create study titles, study identifiers,
        and associated organizations. It handles both standard predefined organizations and
        custom non-standard organizations.

        Args:
            data (dict): A complex dictionary containing study identification information with the following structure:
                {
                    "titles": {
                        "brief": str,           # Brief study title
                        "official": str,        # Official study title
                        "public": str,          # Public study title
                        "scientific": str,      # Scientific study title
                        "acronym": str,         # Study acronym
                    },
                    "identifiers": [            # List of study identifiers
                        {
                            "identifier": str,  # The actual identifier value
                            "scope": {          # Organization scope for the identifier
                                # Either use a standard predefined organization:
                                "standard": str,    # Key from STANDARD_ORGS (e.g., "nct", "ema", "fda")

                                # OR define a custom non-standard organization:
                                "non_standard": {
                                    "type": str,            # Organization type (must match ORG_CODES keys)
                                    "role": str,            # Organization role (must match ROLE_CODES keys), can be None
                                    "name": str,            # Organization name
                                    "description": str,     # Organization description
                                    "label": str,           # Organization label/display name
                                    "identifier": str,      # Organization identifier
                                    "identifierScheme": str, # Scheme used for organization identifier
                                    "legalAddress": {       # Organization's legal address
                                        "lines": [str],     # Address lines (array of strings)
                                        "city": str,        # City name
                                        "district": str,    # District/region
                                        "state": str,       # State/province
                                        "postalCode": str,  # Postal/ZIP code
                                        "country": str      # ISO 3166 country code
                                    }
                                }
                            }
                        }
                    ],
                    "roles": {
                        "co_sponsor": {"name": [str], "legal_address": [address structure]},
                        "local_sponsor": {"name": [str], "legal_address": [address structure]},
                        "device_manufacturer": {"name": [str], "legal_address": [address structure]},
                    }
                }

        Note:
            - Title types must be one of: "brief", "official", "public", "scientific", "acronym"
            - Organization types for non_standard must match keys in ORG_CODES
            - Standard organization keys must match keys in STANDARD_ORGS
            - Country codes must be valid ISO 3166 codes
            - Each identifier must have either "standard" OR "non_standard" in scope, not both

        Raises:
            Various exceptions may be raised during object creation if data is invalid
        """
        # Make sure data ok.
        titles = data["titles"] if "titles" in data else {}
        identifiers = data["identifiers"] if "identifiers" in data else []
        roles = data["roles"] if "roles" in data else {}
        # Titles
        for type, text in titles.items():
            try:
                if type in self.TITLE_TYPES:
                    title = self._create_title(type, text)
                    if title:
                        self._titles.append(title)
                else:
                    self._errors.warning(
                        f"Title '{text}' of type '{type}' is not valid, ignored."
                    )
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of title '{text}' of type '{type}'",
                    e,
                    KlassMethodLocation(self.MODULE, "execute"),
                )

        # Identifiers
        id_details: dict
        for id_details in identifiers:
            try:
                scope = id_details["scope"]
                organization: dict = (
                    copy.deepcopy(self.STANDARD_ORGS[scope["standard"]])
                    if "standard" in scope
                    else scope["non_standard"]
                )

                # Address
                if organization["legalAddress"]:
                    organization["legalAddress"] = self._create_address(
                        organization["legalAddress"]
                    )

                # Identifier and scoping Organization
                org = self._create_organization(organization)
                if org:
                    scope_key = scope["standard"] if "standard" in scope else "other"
                    identifier = self._create_identifier(
                        scope_key, id_details["identifier"], org
                    )
                    if identifier:
                        self._organizations.append(org)
                        self._identifiers.append(identifier)
                    else:
                        self._errors.exception(
                            f"Failed to create identifier {id_details['identifier']} from organization '{organization}'",
                            KlassMethodLocation(self.MODULE, "execute"),
                        )
                else:
                    self._errors.exception(
                        f"Failed to create organization {organization}",
                        KlassMethodLocation(self.MODULE, "execute"),
                    )
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of identifier {id_details}",
                    e,
                    KlassMethodLocation(self.MODULE, "execute"),
                )
        for role, info in roles.items():
            try:
                self._errors.debug(
                    f"Processing {role}, {info}",
                    KlassMethodLocation(self.MODULE, "execute"),
                )
                if info is None:
                    continue
                organization = copy.deepcopy(self.ROLE_ORGS[role])
                organization["label"] = info["name"]
                organization["legalAddress"] = (
                    self._create_address(info["address"]) if "address" in info else None
                )
                org = self._create_organization(organization)
                if org:
                    self._errors.debug(
                        f"Organization {org} in {role} created",
                        KlassMethodLocation(self.MODULE, "execute"),
                    )
                    self._organizations.append(org)
                else:
                    self._errors.exception(
                        f"Failed to create organization in {role}, {organization}",
                        KlassMethodLocation(self.MODULE, "execute"),
                    )
            except Exception as e:
                self._errors.exception(
                    f"Failed during creation of organization in {role}, {info}",
                    e,
                    KlassMethodLocation(self.MODULE, "execute"),
                )
        if "other" in data:
            if "medical_expert" in data["other"]:
                me: dict
                me = data["other"]["medical_expert"]
                if me: 
                    if me.get("name"):
                        ap: AssignedPerson = self._create_assigned_person(me)
                        if ap:
                            role: StudyRole = self._create_role("medical expert")
                            if role:
                                role.assignedPersons = [ap]
                    elif me.get("reference"):
                        self._medical_expert_contact_details_location = ("/n").join(me["reference"])
                    else:
                        self._errors.warning(
                            f"No medical expert contact information detected",
                            KlassMethodLocation(self.MODULE, "execute"),
                        )
            self._sponsor_signatory = data["other"]["sponsor_signatory"]
            self._compound_names = data["other"]["compound_names"]
            self._compound_codes = data["other"]["compound_codes"]

    @property
    def titles(self):
        return self._titles

    @property
    def organizations(self):
        return self._organizations

    @property
    def identifiers(self):
        return self._identifiers

    @property
    def roles(self):
        return self._roles

    @property
    def sponsor_signatory(self) -> str:
        return self._sponsor_signatory

    @property
    def compound_names(self) -> str:
        return self._compound_names

    @property
    def medical_expert_contact_details_location(self) -> str | None:
        return self._medical_expert_contact_details_location

    @property
    def compound_codes(self) -> str:
        return self._compound_codes

    def _create_address(self, address: dict) -> Address | None:
        try:
            self._errors.debug(
                f"Creating address, source data: {address}",
                KlassMethodLocation(self.MODULE, "_create_address"),
            )
            if ("country" in address) and address["country"]:
                address["country"] = self._builder.iso3166_code_or_decode(
                    address["country"]
                )
            else:
                address["country"] = None
            addr: Address = self._builder.create(Address, address)
            addr.set_text()
            self._errors.info(
                f"Address set to {addr.text}",
                KlassMethodLocation(self.MODULE, "_create_address"),
            )
            return addr
        except Exception as e:
            self._errors.exception(
                "Failed to create address object",
                e,
                KlassMethodLocation(self.MODULE, "_create_address"),
            )
            return None

    def _create_organization(self, organization: dict) -> Organization | None:
        try:
            role = None
            if organization["role"]:
                role: StudyRole = self._create_role(organization["role"])
                organization.pop("role")
            org_type = organization["type"]
            organization["type"] = self._builder.cdisc_code(
                self.ORG_CODES[org_type]["code"], self.ORG_CODES[org_type]["decode"]
            )
            organization["name"] = (
                organization["name"]
                if "name" in organization
                else self._label_to_name(organization["label"])
            )
            org = self._builder.create(Organization, organization)
            if role:
                role.organizationIds = [org.id]
            return org
        except Exception as e:
            self._errors.exception(
                "Failed during creation of organization",
                e,
                KlassMethodLocation(self.MODULE, "_create_organization"),
            )
            return None

    def _create_identifier(
        self, scope: str, identifier: str, org: Organization
    ) -> StudyIdentifier | None:
        try:
            type_code = self._identifier_type(scope)
            identifier = self._builder.create(
                StudyIdentifier,
                {
                    "text": identifier,
                    "scopeId": org.id,
                    "extensionAttributes": [type_code],
                },
            )
            return identifier
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of identifier '{identifier}' with scope type '{scope}' and organisation {org}",
                e,
                KlassMethodLocation(self.MODULE, "_create_identifier"),
            )
            return None

    def _identifier_type(self, scope: str) -> ExtensionAttribute:
        if scope in self.IDENTIFIER_CODES:
            code = self.IDENTIFIER_CODES[scope]["code"]
            decode = self.IDENTIFIER_CODES[scope]["decode"]
        else:
            code = self.IDENTIFIER_CODES["other"]["code"]
            decode = self.IDENTIFIER_CODES["other"]["decode"]
        code: Code = self._builder.create(
            Code,
            {
                "code": code,
                "decode": decode,
                "codeSystem": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
                "codeSystemVersion": "25.12e",
            },
        )
        base_code = BaseCode(
            **code.model_dump(
                include={
                    "id",
                    "code",
                    "codeSystem",
                    "codeSystemVersion",
                    "decode",
                    "instanceType",
                }
            )
        )
        return self._builder.create(
            ExtensionAttribute,
            {
                "url": SIT_EXT_URL,
                "valueCode": base_code,
            },
        )

    def _create_title(self, type: str, text: str) -> StudyTitle | None:
        try:
            title_type = self._builder.cdisc_code(
                self.TITLE_CODES[type]["code"], self.TITLE_CODES[type]["decode"]
            )
            return self._builder.create(StudyTitle, {"text": text, "type": title_type})
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of title '{text}'of type '{type}'",
                e,
                KlassMethodLocation(self.MODULE, "_create_title"),
            )
            return None

    def _create_role(self, type: str) -> StudyRole | None:
        try:
            role_type = self._builder.cdisc_code(
                self.ROLE_CODES[type]["code"], self.ROLE_CODES[type]["decode"]
            )
            index = len(self._roles)
            study_role: StudyRole = self._builder.create(
                StudyRole, {"name": f"ROLE_{index + 1}", "code": role_type}
            )
            if study_role:
                self._roles.append(study_role)
            return study_role
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of role of type '{type}'",
                e,
                KlassMethodLocation(self.MODULE, "_create_role"),
            )
            return None

    def _create_assigned_person(self, data: dict) -> AssignedPerson | None:
        try:
            person_name: PersonName = self._builder.create(
                PersonName, {"text": data["name"]}
            )
            ap: AssignedPerson = self._builder.create(
                AssignedPerson,
                {
                    "name": data["name"],
                    "personName": person_name,
                    "jobTitle": "Medical Expert",
                },
            )
            return ap
        except Exception as e:
            self._errors.exception(
                f"Failed during creation of assigned person from {data}",
                e,
                KlassMethodLocation(self.MODULE, "_create_assigned_person"),
            )
            return None
