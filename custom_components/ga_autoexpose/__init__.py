"""Google Assistant Auto-Expose Custom Integration."""
import os
import yaml
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.const import CLOUD_NEVER_EXPOSED_ENTITIES

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ga_autoexpose"
ASSISTANT = "cloud.google_assistant"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Google Assistant Auto-Expose component."""
    async def export_google_assistant_entities(call):
        """Export Google Assistant exposed entities to a file."""
        config_folder = os.path.dirname(hass.config.path("configuration.yaml"))
        output_file = os.path.join(config_folder, "exposed.yaml")

        try:
            # Access the exposed entities manager
            exposed_entities = hass.data.get("homeassistant.exposed_entites")
            entity_registry = async_get_entity_registry(hass)

            if not exposed_entities:
                _LOGGER.error("Could not access exposed entities data.")
                return

            # Fetch the assistant settings and configuration for Google Assistant
            assistant_settings = exposed_entities.async_get_assistant_settings(ASSISTANT)
            ga_config = hass.data["google_assistant"]
            config_data = ga_config.get("config", {})  # Get the nested 'config' dictionary
            expose_by_default = config_data.get("expose_by_default", False)  # Fetch expose_by_default from it
            exposed_domains = config_data.get("exposed_domains", [])  # Fetch exposed_domains from it
            
            _LOGGER.debug("expose_by_default: %s", expose_by_default)
            _LOGGER.debug("exposed_domains: %s", exposed_domains)
            _LOGGER.debug("CLOUD_NEVER_EXPOSED_ENTITIES: %s", CLOUD_NEVER_EXPOSED_ENTITIES)

            # Process and structure the exposed entities
            exposed_entities_data = {}
            for entity_id, settings in assistant_settings.items():

                if entity_id in CLOUD_NEVER_EXPOSED_ENTITIES:
                    _LOGGER.debug("Skipping entity (never exposed): %s", entity_id)
                    continue

                # Check `should_expose` setting
                if not settings.get("should_expose"):
                    # Fallback to expose_by_default and exposed_domains
                    if not expose_by_default:
                        _LOGGER.debug("Skipping entity (not explicitly exposed and expose_by_default is off): %s", entity_id)
                        continue

                    # Check if the entity's domain is allowed to be exposed
                    domain = entity_id.split(".")[0]
                    if domain not in exposed_domains:
                        _LOGGER.debug("Skipping entity (domain not in exposed_domains): %s", entity_id)
                        continue

                _LOGGER.debug("Processing entity: %s", entity_id)

                # Get registry entry for display name and aliases
                registry_entry = entity_registry.async_get(entity_id)
                aliases = list(registry_entry.aliases) if registry_entry and registry_entry.aliases else []

                # Fetch both names
                friendly_name = registry_entry.original_name if registry_entry else None
                google_assistant_name = settings.get("name")

                # Determine the display name (prioritize original_name)
                display_name = friendly_name or google_assistant_name or entity_id

                # Log for debugging
                _LOGGER.debug(
                    "Entity: %s, Friendly Name: %s, Google Assistant Name: %s, Final Name: %s",
                    entity_id,
                    friendly_name,
                    google_assistant_name,
                    display_name,
                )

                exposed_entities_data[entity_id] = {
                    "name": display_name,
                    "aliases": aliases,
                }

            # Write the exposed entities to a YAML file using a thread-safe method
            def write_to_file():
                with open(output_file, "w", encoding="utf-8") as file:
                    yaml.dump(
                        exposed_entities_data,
                        file,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )

            await hass.async_add_executor_job(write_to_file)

            _LOGGER.info(f"Exported {len(exposed_entities_data)} entities to {output_file}")

        except Exception as e:
            _LOGGER.error(f"Error exporting entities: {e}")

    # Register the service
    hass.services.async_register(DOMAIN, "export_entities", export_google_assistant_entities)
    return True
