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
                    if population and "criteria" in population:
                        criteria += population["criteria"]
                        population["criterionIds"] = [
                            x["id"] for x in population["criteria"]
                        ]
                        population.pop("criteria")
                        if "cohorts" in population:
                            for cohorts in population["cohorts"]:
                                criteria += cohorts["criteria"]
                                cohorts["criterionIds"] = [
                                    x["id"] for x in cohorts["criteria"]
                                ]
                                cohorts.pop("criteria")
            version["criteria"] = criteria

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
    def _convert_subject_enrollment(collection: list) -> list:
        for item in collection:
            scope = {
                "id": f"{item['id']}_GeoScope",
                "type": item["type"],
                "code": item["code"],
                "instanceType": "GeographicScope",
            }
            item["forGeographicScope"] = scope
            item["name"] = f"{scope['type']['decode']} - {scope['code']['standardCode']['decode']}"
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
    def _move(data: dict, from_key: str, to_key: str) -> None:
        data[to_key] = data[from_key]
        data.pop(from_key)
