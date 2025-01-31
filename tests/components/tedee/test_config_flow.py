"""Test the Tedee config flow."""
from unittest.mock import MagicMock

from pytedee_async import TedeeClientException, TedeeLocalAuthException
import pytest

from homeassistant import config_entries
from homeassistant.components.tedee.const import CONF_LOCAL_ACCESS_TOKEN, DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

FLOW_UNIQUE_ID = "112233445566778899"
LOCAL_ACCESS_TOKEN = "api_token"


async def test_flow(hass: HomeAssistant, mock_tedee: MagicMock) -> None:
    """Test config flow with one bridge."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.62",
            CONF_LOCAL_ACCESS_TOKEN: "token",
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_HOST: "192.168.1.62",
        CONF_LOCAL_ACCESS_TOKEN: "token",
    }


async def test_flow_already_configured(
    hass: HomeAssistant,
    mock_tedee: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test config flow aborts when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.62",
            CONF_LOCAL_ACCESS_TOKEN: "token",
        },
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (TedeeClientException("boom."), {CONF_HOST: "invalid_host"}),
        (
            TedeeLocalAuthException("boom."),
            {CONF_LOCAL_ACCESS_TOKEN: "invalid_api_key"},
        ),
    ],
)
async def test_config_flow_errors(
    hass: HomeAssistant,
    mock_tedee: MagicMock,
    side_effect: Exception,
    error: dict[str, str],
) -> None:
    """Test the config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM

    mock_tedee.get_local_bridge.side_effect = side_effect

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.42",
            CONF_LOCAL_ACCESS_TOKEN: "wrong_token",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == error
    assert len(mock_tedee.get_local_bridge.mock_calls) == 1
