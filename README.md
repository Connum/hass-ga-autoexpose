# Home Assistant Custom Component: Google Assistant Auto-Expose

Tired of having to add all the devices to expose for your local Google Assistant integration to the `google_assistant.entity_config` key in your **configuration.yaml**, while the cloud subscribers get to configure them easily via the UI?
This custom component automatically exports all the exposed entities configured in Home Assistant's UI for Google Assistant if you are using a local integration instead of the cloud integration.

## Note

This was hacked together quickly and is not yet ready to be moved to HACS. It assumes you have set up a working local Google Assistant integration (see https://github.com/home-assistant/home-assistant.io/issues/35867#issuecomment-2494797373 for updated instructions since Google has sunset Conversational Actions).

## Installation

Manually install into the `custom_components` directory in your config directory (at your own risk) and then restart Home Assistant.

## Usage

You will then have a new action (formerly called "service") `ga_autoexpose.export_entities`, which exports all the exposed entities configured under `Settings > Voice assistants` into a file **exposed.yaml** in your config folder.

Include this file as the `entity_config` content in the `google_assistant` section of your **configuration.yaml** in your config folder, e.g:

```yaml
google_assistant:
  project_id: ***
  service_account: !include SERVICE_ACCOUNT.JSON
  report_state: true
  expose_by_default: false
  exposed_domains:
    - switch
    - light
  entity_config: !include exposed.yaml
```

**Important:** The cloud integration must still be active (i.e. you must be logged in under `Settings > Home Assistant Cloud`) in order to be able to use the UI to configure the exposal, but it doesn't need an active subscription.
I'll look into enabling the UI even with a completely disabled cloud service, if I find the time necessary. But PRs are welcome if others would like to contribute.

You should call this action before you call `google_assistant.request_sync`, so best make an automation that calls the two actions consecutively in order to get your latest device changes into your Google Assistant / Home app.
