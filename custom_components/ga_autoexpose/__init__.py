"""Google Assistant Auto-Expose Custom Integration."""
import os
import yaml
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

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

            # Fetch all assistant settings for Google Assistant
            assistant_settings = exposed_entities.async_get_assistant_settings(ASSISTANT)

            # Process and structure the exposed entities
            exposed_entities_data = {}
            for entity_id, settings in assistant_settings.items():
                if settings.get("should_expose"):
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
                else:
                    _LOGGER.debug("Skipping entity: %s", entity_id)

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
