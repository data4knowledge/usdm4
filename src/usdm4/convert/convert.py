from usdm4.__version__ import __model_version__
from usdm4.api.wrapper import Wrapper


class Convert:
    @classmethod
    def convert(cls, data: dict) -> dict:
        wrapper = data
        study = wrapper["study"]

        # Chnage the wrapper details
        wrapper["usdmVersion"] = __model_version__
        wrapper["systemName"] = "Python USDM4 Package"

        # Change type of documents
        if study["documentedBy"]:
            study["documentedBy"]["instanceType"] = "StudyDefinitionDocument"
            study["documentedBy"]["language"] = {
                "id": "LangaugeCode_1",
                "code": "en",
                "codeSystem": "ISO 639-1",
                "codeSystemVersion": "2007",
                "decode": "English",
                "instanceType": "Code",
            }
            study["documentedBy"]["documentType"] = {
                "id": "DocumentTypeCode_1",
                "code": "C70817",
                "codeSystem": "cdisc.org",
                "codeSystemVersion": "2023-12-15",
                "decode": "Study Protocol",
                "instanceType": "Code",
            }
            study["documentedBy"]["type"] = {
                "id": "DocumentTypeCode_1",
                "code": "C70817",
                "codeSystem": "cdisc.org",
                "codeSystemVersion": "2023-12-15",
                "decode": "Protocol",
                "instanceType": "Code",
            }
            study["documentedBy"]["templateName"] = "Sponsor Study Protocol Template"
            for versions in study["documentedBy"]["versions"]:
                Convert._move(versions, "protocolStatus", "status")
                Convert._move(versions, "protocolVersion", "version")
            study["documentedBy"] = [study["documentedBy"]]

        for version in study["versions"]:
            doc_id = version["documentVersionId"]
            doc = cls._get_document(study, doc_id)
            if doc:
                doc["instanceType"] = "StudyDefinitionDocumentVersion"
                items = []
                for content in doc["contents"]:
                    content["displaySectionTitle"] = True
                    content["displaySectionNumber"] = True
                    id = f"{content['id']}_ITEM"
                    items.append(
                        {
                            "id": id,
                            "name": content["name"],
                            "text": content["text"],
                            "instanceType": "NarrativeContentItem",
                        }
                    )
                version["narrativeContentItems"] = items

        # StudyVersion
        for version in study["versions"]:
            version["documentVersionIds"] = [version["documentVersionId"]]
            version.pop("documentVersionId")
            version["referenceIdentifiers"] = []
            version["abbreviations"] = []
            version["roles"] = []
            version["administrableProducts"] = []
            version["notes"] = []

            # Need to be populated
            version["criteria"] = []

            # Move the organization to a StudyVersion collection
            organizations = []
            for identifier in version["studyIdentifiers"]:
                Convert._move(identifier, "studyIdentifier", "text")
                org = identifier["studyIdentifierScope"]
                organizations.append(org)
                Convert._move(org, "organizationType", "type")
                identifier["scopeId"] = org["id"]
                identifier.pop("studyIdentifierScope")
            version["organizations"] = organizations

            # Move the criteria to a StudyVersion collection
            criteria = []
            for study_design in version["studyDesigns"]:
                if "population" in study_design:
                    population = study_design["population"]
                    population = Convert._convert_population(population, criteria)
                    if "cohorts" in population:
                        for cohort in population["cohorts"]:
                            cohort = Convert._convert_population(cohort, criteria)
            version["criteria"] = criteria

            for study_design in version["studyDesigns"]:
                # if "blindingSchema" in study_design:
                #    study_design["blindingSchema"] = Convert._convert_code_to_alias(study_design["blindingSchema"])
                Convert._move(study_design, "trialIntentTypes", "intentTypes")
                Convert._move(study_design, "trialTypes", "subTypes")
                Convert._move(study_design, "interventionModel", "model")
                study_design["studyPhase"] = version["studyPhase"]
                version.pop("studyPhase")
                study_design["studyType"] = version["studyType"]
                version.pop("studyType")

            # Process the amendments
            for amendment in version["amendments"]:
                Convert._convert_subject_enrollment(amendment["enrollments"])
                amendment["geographicScopes"] = [
                    {
                        "id": f"{amendment['id']}_GeoScope",
                        "type": {
                            "id": f"{amendment['id']}_GeoScopeType",
                            "code": "C68846",
                            "codeSystem": "cdisc.org",
                            "codeSystemVersion": "2023-12-15",
                            "decode": "Global",
                            "instanceType": "Code",
                        },
                        "instanceType": "GeographicScope",
                    }
                ]
        return Wrapper.model_validate(wrapper)

    @staticmethod
    def _convert_population(population: dict, criteria: list) -> dict:
        if "plannedAge" in population:
            population["plannedAge"] = Convert._convert_range(
                population["plannedAge"]
            )
        if "plannedCompletionNumber" in population:
            population["plannedCompletionNumberRange"] = Convert._convert_range(
                population["plannedCompletionNumber"]
            )
            population.pop("plannedCompletionNumber")
        if "plannedEnrollmentNumber" in population:
            population["plannedEnrollmentNumberRange"] = Convert._convert_range(
                population["plannedEnrollmentNumber"]
            )
            population.pop("plannedEnrollmentNumber")
        if "criteria" in population:
            criteria += population["criteria"]
            population["criterionIds"] = [x["id"] for x in criteria]
            population.pop("criteria")
        return population

    @staticmethod
    def _convert_subject_enrollment(collection: list) -> list:
        for item in collection:
            scope = {
                "id": f"{item['id']}_GeoScope",
                "type": item["type"],
                "code": item["code"],
                "instanceType": "GeographicScope",
            }
            item["forGeographicScope"] = scope
            item["name"] = (
                f"{scope['type']['decode']} - {scope['code']['standardCode']['decode']}"
            )
            item.pop("type")
            item.pop("code")
        return collection

    @staticmethod
    def _get_document(study: dict, doc_id: str):
        if study["documentedBy"]:
            for doc in study["documentedBy"][0]["versions"]:
                if doc["id"] == doc_id:
                    return doc
        return None

    @staticmethod
    def _convert_range(range: dict) -> dict:
        print(f"RANGE: {range}")
        for item in ["min", "max"]:
            key = f"{item}Value"
            if range["unit"]:
                unit = Convert._convert_code_to_alias(range["unit"])
                unit["id"] = f"{range['unit']['id']}_Unit"
            else:
                unit = None
            range[key] = {
                "id": f"{range['id']}_Min",
                "value": range[key],
                "unit": unit,
                "instanceType": "Quantity",
            }
        range.pop("unit")
        return range

    @staticmethod
    def _convert_code_to_alias(code: dict) -> dict:
        print(f"ALIAS CODE: {code}")
        return {
            "id": f"{code['id']}_AliasCode",
            "standardCode": code,
            "standardAliasCode": [],
            "instanceType": "AliasCode",
        }

    @staticmethod
    def _move(data: dict, from_key: str, to_key: str) -> None:
        data[to_key] = data[from_key]
        data.pop(from_key)
