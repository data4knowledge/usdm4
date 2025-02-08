class Convert:
    
    @classmethod
    def convert(cls, data: dict) -> dict:
        wrapper = data
        study = wrapper["study"]

        # Chnage the wrapper details
        wrapper["usdmVersion"] = "3.6.0"

        # Change type of documents
        if study["documentedBy"]:
            study["documentedBy"]["instanceType"] = "StudyDefinitionDocument"

        for version in study["versions"]:
            doc_id = version["documentVersionId"]
            doc = cls._get_document(study, doc_id)
            if doc:
                doc["instanceType"] = "StudyDefinitionDocumentVersion"
                items = []
                for content in doc["contents"]:
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
                org = identifier["studyIdentifierScope"]
                organizations.append(org)
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
        return wrapper

    @staticmethod
    def _get_document(study: dict, doc_id: str):
        if study["documentedBy"]:
            for doc in study["documentedBy"]["versions"]:
                if doc["id"] == doc_id:
                    return doc
        return None
