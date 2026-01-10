"""Config flow for Lyngdorf integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    COMPATIBLE_MODELS,
    CONF_BAUD_RATE,
    CONF_MODEL,
    CONF_SOURCES,
    CONF_ZONE2_DEFAULT_SOURCE,
    CONF_ZONE2_ENABLED,
    CONF_ZONE2_MAX_VOLUME,
    DEFAULT_URL,
    DEFAULT_ZONE2_ENABLED,
    DEFAULT_ZONE2_MAX_VOLUME,
    DOMAIN,
)
from .pylyngdorf import async_get_lyngdorf
from .pylyngdorf.models import AUDIO_INPUTS
from .utils import get_connection_overrides

LOG = logging.getLogger(__name__)

# supported baud rates for Lyngdorf devices
BAUD_RATES = [9600, 19200, 38400, 57600, 115200]


class UnsupportedDeviceError(HomeAssistantError):
    """Error for unsupported device types."""


class LyngdorfConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lyngdorf."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,  # noqa: ARG004
    ) -> LyngdorfOptionsFlow:
        """Get the options flow for this handler."""
        return LyngdorfOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step of selecting model to configure."""
        errors: dict[str, str] = {}

        if user_input is not None:
            LOG.info(f'Config flow user input: {user_input}')

            model_id = user_input[CONF_MODEL]
            url = user_input.get('url', '').strip()

            try:
                loop = asyncio.get_event_loop()
                config_overrides = get_connection_overrides(user_input)

                # connect to the device to confirm everything works
                client = await async_get_lyngdorf(model_id, url, loop, **config_overrides)

                # test connection with ping
                if not await client.device.ping():
                    raise ConnectionError('Device did not respond to ping')

                # unique_id is url + model (Lyngdorf doesn't expose serial via RS232)
                unique_id = f'{model_id}_{url}'

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

            except ConnectionError as e:
                errors['base'] = 'cannot_connect'
                LOG.warning(f'Failed config_flow: {errors}', exc_info=e)
            except UnsupportedDeviceError as e:
                errors['base'] = 'unsupported'
                LOG.warning(f'Failed config_flow: {errors}', exc_info=e)
            except Exception as e:
                errors['base'] = 'cannot_connect'
                LOG.exception(f'Unexpected error in config_flow: {e}')
            else:
                return self.async_create_entry(title='Lyngdorf', data=user_input)

        # build model options for selector
        model_options = [
            SelectOptionDict(value=model, label=model.upper()) for model in COMPATIBLE_MODELS
        ]

        # build baud rate options
        baud_options = [SelectOptionDict(value=str(rate), label=str(rate)) for rate in BAUD_RATES]

        data_schema = {
            CONF_MODEL: SelectSelector(
                SelectSelectorConfig(
                    options=model_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            'url': TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.TEXT,
                )
            ),
            CONF_BAUD_RATE: SelectSelector(
                SelectSelectorConfig(
                    options=baud_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }

        return self.async_show_form(
            step_id='user',
            data_schema=self.add_suggested_values_to_schema(
                self._schema_from_selectors(data_schema),
                {'url': DEFAULT_URL, CONF_BAUD_RATE: '115200'},
            ),
            errors=errors,
        )

    def _schema_from_selectors(self, selectors: dict[str, Any]) -> dict[str, Any]:
        """Convert selector dict to voluptuous schema."""
        import voluptuous as vol

        schema = {}
        for key, selector in selectors.items():
            # model and url are required, baud rate is optional
            if key in (CONF_MODEL, 'url'):
                schema[vol.Required(key)] = selector
            else:
                schema[vol.Optional(key)] = selector
        return vol.Schema(schema)


class LyngdorfOptionsFlow(OptionsFlow):
    """Handle options flow for the component."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options for the custom component."""
        return self.async_show_menu(
            step_id='init',
            menu_options=['connection', 'sources', 'zone2'],
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure connection settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # convert baud rate back to int if provided
            if CONF_BAUD_RATE in user_input and user_input[CONF_BAUD_RATE]:
                user_input[CONF_BAUD_RATE] = int(user_input[CONF_BAUD_RATE])
            return self.async_create_entry(title='', data=user_input)

        current_url = self.config_entry.options.get(
            'url', self.config_entry.data.get('url', DEFAULT_URL)
        )
        current_baud = self.config_entry.options.get(
            CONF_BAUD_RATE, self.config_entry.data.get(CONF_BAUD_RATE, 115200)
        )

        baud_options = [SelectOptionDict(value=str(rate), label=str(rate)) for rate in BAUD_RATES]

        data_schema = {
            'url': TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            CONF_BAUD_RATE: SelectSelector(
                SelectSelectorConfig(
                    options=baud_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }

        return self.async_show_form(
            step_id='connection',
            data_schema=self.add_suggested_values_to_schema(
                self._schema_from_selectors(data_schema),
                {'url': current_url, CONF_BAUD_RATE: str(current_baud)},
            ),
            errors=errors,
        )

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure custom source names."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # filter out empty source names and convert to dict
            sources_config = {}
            for key, value in user_input.items():
                if value and value.strip():
                    # extract source number from key (e.g., 'source_0' -> 0)
                    source_id = int(key.split('_')[1])
                    sources_config[source_id] = value.strip()

            # merge with existing options, preserving other settings
            updated_options = dict(self.config_entry.options)
            updated_options[CONF_SOURCES] = sources_config
            return self.async_create_entry(title='', data=updated_options)

        # get current source configuration
        current_sources = self.config_entry.options.get(
            CONF_SOURCES, self.config_entry.data.get(CONF_SOURCES, {})
        )

        # build schema with commonly used sources
        common_sources = [1] + list(range(3, 13)) + [24]
        import voluptuous as vol

        schema_dict = {}
        for source_id in common_sources:
            default_name = current_sources.get(source_id, AUDIO_INPUTS.get(source_id, ''))
            schema_dict[vol.Optional(f'source_{source_id}', default=default_name)] = TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            )

        return self.async_show_form(
            step_id='sources',
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_zone2(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Configure Zone 2 settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # merge with existing options, preserving other settings
            updated_options = dict(self.config_entry.options)
            updated_options[CONF_ZONE2_ENABLED] = user_input.get(
                CONF_ZONE2_ENABLED, DEFAULT_ZONE2_ENABLED
            )

            if user_input.get(CONF_ZONE2_ENABLED):
                # only save zone 2 settings if enabled
                if user_input.get(CONF_ZONE2_DEFAULT_SOURCE) is not None:
                    updated_options[CONF_ZONE2_DEFAULT_SOURCE] = user_input[
                        CONF_ZONE2_DEFAULT_SOURCE
                    ]
                updated_options[CONF_ZONE2_MAX_VOLUME] = user_input.get(
                    CONF_ZONE2_MAX_VOLUME, DEFAULT_ZONE2_MAX_VOLUME
                )
            else:
                # remove zone 2 settings if disabled
                updated_options.pop(CONF_ZONE2_DEFAULT_SOURCE, None)
                updated_options.pop(CONF_ZONE2_MAX_VOLUME, None)

            return self.async_create_entry(title='', data=updated_options)

        # get current zone 2 configuration
        current_zone2_enabled = self.config_entry.options.get(
            CONF_ZONE2_ENABLED,
            self.config_entry.data.get(CONF_ZONE2_ENABLED, DEFAULT_ZONE2_ENABLED),
        )
        current_zone2_default_source = self.config_entry.options.get(
            CONF_ZONE2_DEFAULT_SOURCE,
            self.config_entry.data.get(CONF_ZONE2_DEFAULT_SOURCE),
        )
        current_zone2_max_volume = self.config_entry.options.get(
            CONF_ZONE2_MAX_VOLUME,
            self.config_entry.data.get(CONF_ZONE2_MAX_VOLUME, DEFAULT_ZONE2_MAX_VOLUME),
        )

        # create list of source options for dropdown
        source_options = [
            SelectOptionDict(value=str(source_id), label=name)
            for source_id, name in sorted(AUDIO_INPUTS.items(), key=lambda x: x[0])
            if source_id > 0  # exclude 'None'
        ]

        import voluptuous as vol

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ZONE2_ENABLED, default=current_zone2_enabled): BooleanSelector(),
                vol.Optional(
                    CONF_ZONE2_DEFAULT_SOURCE, default=current_zone2_default_source
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=source_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_ZONE2_MAX_VOLUME, default=current_zone2_max_volume
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=-99.9,
                        max=24.0,
                        step=0.1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement='dB',
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id='zone2',
            data_schema=data_schema,
            errors=errors,
        )

    def _schema_from_selectors(self, selectors: dict[str, Any]) -> dict[str, Any]:
        """Convert selector dict to voluptuous schema."""
        import voluptuous as vol

        schema = {}
        for key, selector in selectors.items():
            schema[vol.Optional(key)] = selector
        return vol.Schema(schema)
