from datetime import datetime
import pytest

from .thermostat import Device, SetpointMode, SystemMode, thermostat_client
from .errors import RequestClientException, UnsuportedArgumentsException

token = {
    "access_token": "12345",
    "refresh_token": "abcde",
    "expires_at": "",
    "expires_in": ""
}

get_thermostats_data_request = {
    "device_type": "NAVaillant",
    "access_token": "12345",
}

get_thermostats_data_response = {
    "status": "ok",
    "body": {
        "devices": [
            {
                "_id": "id",
                "type": "type",
                "station_name": "station_name",
                "firmware": "firmware",
                "system_mode": "summer",
                "setpoint_default_duration": 120,
                "setpoint_hwb": {"setpoint_activate": False},
                "modules": [
                    {
                        "_id": "id",
                        "type": "type",
                        "module_name": "module_name",
                        "firmware": "firmware",
                        "setpoint_away": {"setpoint_activate": False},
                        "setpoint_manual": {"setpoint_activate": False},
                        "measured": {"temperature": 25, "setpoint_temp": 26, "est_setpoint_temp": 27},
                    }
                ]
            }
        ]
    }
}

set_system_mode_request = {
    "device_id": "device",
    "module_id": "module",
    "system_mode": "summer",
    "access_token": "12345",
}

set_system_mode_response = {
    "status": "ok",
}

set_minor_mode_request = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "away",
    "activate": True,
    "access_token": "12345",
}

set_minor_mode_response = {
    "status": "ok",
}

@pytest.mark.asyncio
class TestThermostat:
    async def test_async_get_thermostats_data__invalid_request_params__raises_error(self, respx_mock):
        respx_mock.post("https://api.netatmo.com/api/getthermostatsdata", data=get_thermostats_data_request).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException):
                await client.async_get_thermostats_data()

    async def test_async_get_thermostats_data__valid_request_params__returns_valid_device_list(self, respx_mock):
        respx_mock.post("https://api.netatmo.com/api/getthermostatsdata", data=get_thermostats_data_request).respond(200, json=get_thermostats_data_response)

        async with thermostat_client("", "", token, None) as client:
            devices = await client.async_get_thermostats_data()

            expected_devices = get_thermostats_data_response["body"]["devices"]

            assert len(devices) == len(expected_devices)
            for x in zip(devices, expected_devices):
                assert x[0] == Device(**x[1])

    async def test_async_set_system_mode__invalid_request_params__raises_error(self, respx_mock):
        respx_mock.post("https://api.netatmo.com/api/setsystemmode", data=set_system_mode_request).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException):
                await client.async_set_system_mode(set_system_mode_request["device_id"], set_system_mode_request["module_id"], SystemMode.SUMMER)

    async def test_async_set_system_mode__valid_request_params__doesnt_raise_error(self, respx_mock):
        respx_mock.post("https://api.netatmo.com/api/setsystemmode", data=set_system_mode_request).respond(200, json=set_system_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_system_mode(set_system_mode_request["device_id"], set_system_mode_request["module_id"], SystemMode.SUMMER)

    async def test_async_set_minor_mode__invalid_request_params__raises_error(self, respx_mock):
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException):
                await client.async_set_minor_mode(set_minor_mode_request["device_id"], set_minor_mode_request["module_id"], SetpointMode.AWAY, True)

    async def test_async_set_minor_mode__activate_manual_without_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.MANUAL,
                    True,
                )
    
    async def test_async_set_minor_mode__activate_manual_without_temp__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.MANUAL,
                    True,
                    setpoint_endtime=datetime.now(),
                )
    
    async def test_async_set_minor_mode__activate_manual_without_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.MANUAL,
                    True,
                    setpoint_temp=25,
                )

    async def test_async_set_minor_mode__activate_manual_with_temp_and_endtime__executes_successfully(self, respx_mock):
        endtime = round(datetime.now().timestamp()) + 1 # unix epoch timestamp

        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "manual",
            "activate": True,
            "setpoint_endtime": endtime,
            "setpoint_temp": 25,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.MANUAL,
                True,
                setpoint_endtime=datetime.fromtimestamp(endtime),
                setpoint_temp=25,
            )

    async def test_async_set_minor_mode__deactivate_manual_with_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.MANUAL,
                    False,
                    setpoint_temp=25,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_manual_with_temp__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.MANUAL,
                    False,
                    setpoint_temp=25,
                )
    
    async def test_async_set_minor_mode__deactivate_manual_with_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.MANUAL,
                    False,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_manual_without_temp_and_endtime__executes_successfully(self, respx_mock):
        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "manual",
            "activate": False,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.MANUAL,
                False,
            )

    async def test_async_set_minor_mode__activate_away_without_temp_and_endtime__executes_successfully(self, respx_mock):
        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "away",
            "activate": True,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.AWAY,
                True,
            )

    async def test_async_set_minor_mode__activate_away_without_temp__executes_successfully(self, respx_mock):
        endtime = round(datetime.now().timestamp()) + 1 # unix epoch timestamp
        
        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "away",
            "activate": True,
            "setpoint_endtime": endtime,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.AWAY,
                True,
                setpoint_endtime=datetime.fromtimestamp(endtime),
            )
    
    async def test_async_set_minor_mode__activate_away_without_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.AWAY,
                    True,
                    setpoint_temp=25,
                )
    
    async def test_async_set_minor_mode__activate_away_with_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.AWAY,
                    True,
                    setpoint_temp=25,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_away_with_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.AWAY,
                    False,
                    setpoint_temp=25,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_away_with_temp__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.AWAY,
                    False,
                    setpoint_temp=25,
                )
    
    async def test_async_set_minor_mode__deactivate_away_with_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.AWAY,
                    False,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_away_without_temp_and_endtime__executes_successfully(self, respx_mock):
        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "away",
            "activate": False,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.AWAY,
                False,
            )

    async def test_async_set_minor_mode__activate_hwb_without_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    True,
                )

    async def test_async_set_minor_mode__activate_hwb_without_temp__executes_successfully(self, respx_mock):
        endtime = round(datetime.now().timestamp()) + 1 # unix epoch timestamp

        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "away",
            "activate": True,
            "setpoint_endtime": endtime,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.AWAY,
                True,
                setpoint_endtime=datetime.fromtimestamp(endtime),
            )
    
    async def test_async_set_minor_mode__activate_hwb_without_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    True,
                    setpoint_temp=25,
                )
    
    async def test_async_set_minor_mode__activate_hwb_with_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    True,
                    setpoint_temp=25,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_hwb_with_temp_and_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    False,
                    setpoint_temp=25,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_hwb_with_temp__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    False,
                    setpoint_temp=25,
                )
    
    async def test_async_set_minor_mode__deactivate_hwb_with_endtime__raises_error(self):
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException):
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    False,
                    setpoint_endtime=datetime.now(),
                )

    async def test_async_set_minor_mode__deactivate_hwb_without_temp_and_endtime__executes_successfully(self, respx_mock):
        set_minor_mode_request = {
            "device_id": "device",
            "module_id": "module",
            "setpoint_mode": "hwb",
            "activate": False,
            "access_token": "12345",
        }

        set_minor_mode_response = {
            "status": "ok",
        }
        
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_request).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.HWB,
                False,
            )