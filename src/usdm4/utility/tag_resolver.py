from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm3.data_store.data_store import DataStore
from usdm4.utility.soup import get_soup, BeautifulSoup

class TagResolver():
    MODULE = "usdm4.utility.tag_resolver.TagResolver"

    def __init__(self, data_store: DataStore, errors: Errors):
        self._data_store = data_store
        self._errors = errors

    def translate(self, instance: dict, text: str) -> str:
        return self._translate_references(instance, text)

    def _translate_references(self, instance: dict, text: str) -> str:
        soup = get_soup(text, self._errors)
        ref: BeautifulSoup
        for ref in soup(["usdm:ref", "usdm:tag"]):
            try:
                if ref.name == "usdm:ref":
                    text = self._resolve_usdm_ref(instance, ref)
                    ref.replace_with(self._translate_references(instance, text))
                if ref.name == "usdm:tag":
                    text = self._resolve_usdm_tag(instance, ref)
                    ref.replace_with(self._translate_references(instance, text))
            except Exception as e:
                self._errors.exception(
                    f"Exception raised while attempting to translate '{ref}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_translate_references")
                )
        return str(soup)
    
    def _resolve_usdm_ref(self, instance: dict, ref: BeautifulSoup) -> str:
        attributes = ref.attrs
        instance = self._data_store.instance_by_id(attributes["id"])
        value = str(instance[attributes["attribute"]])
        return value

    def _resolve_usdm_tag(self, instance: dict, ref: BeautifulSoup) -> str:
        attributes = ref.attrs
        dictionary = self._data_store.instance_by_id(instance["dictionaryId"])
        if dictionary:
            for p_map in dictionary["parameterMaps"]:
                if p_map["tag"] == attributes["name"]:
                    value = p_map["reference"]
                    return value
        self._errors.warning(f"Failed to resolve tag '{ref.name}' in instance '{instance["id"]}'",
                    KlassMethodLocation(self.MODULE, "_resolve_usdm_tag"))
        return f"<i>failed to resolve tag '{ref.name}' in instance '{instance["id"]}'</i>"
