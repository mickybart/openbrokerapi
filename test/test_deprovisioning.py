import http
from unittest.mock import Mock

from flask_testing import TestCase
from werkzeug.wrappers import Response

from cfbrokerapi import _create_app, errors
from cfbrokerapi.service_broker import DeprovisionServiceSpec


class DeprovisioningTest(TestCase):
    def create_app(self):
        from cfbrokerapi.service_broker import ServiceBroker
        self.broker: ServiceBroker = Mock()

        app = _create_app(service_broker=self.broker)
        return app

    def test_returns_200_if_deleted(self):
        self.broker.deprovision.return_value = DeprovisionServiceSpec(False, "operation_str")

        response: Response = self.client.delete(
            "/v2/service_instances/abc?service_id=service-id-here&plan_id=plan-id-here",
            headers={
                'X-Broker-Api-Version': '2.00'
            })

        self.assertEquals(response.status_code, http.HTTPStatus.OK)
        self.assertEquals(response.json, dict())

    def test_returns_202_if_deletion_is_in_progress(self):
        self.broker.deprovision.return_value = DeprovisionServiceSpec(True, "operation_str")

        response: Response = self.client.delete(
            "/v2/service_instances/abc?service_id=service-id-here&plan_id=plan-id-here",
            headers={
                'X-Broker-Api-Version': '2.00'
            })

        self.assertEquals(response.status_code, http.HTTPStatus.ACCEPTED)
        self.assertEquals(response.json, dict(operation="operation_str"))

    def test_returns_410_if_service_instance_already_gone(self):
        self.broker.deprovision.side_effect = errors.ErrInstanceDoesNotExist()

        response: Response = self.client.delete(
            "/v2/service_instances/abc?service_id=service-id-here&plan_id=plan-id-here",
            headers={
                'X-Broker-Api-Version': '2.00'
            })

        self.assertEquals(response.status_code, http.HTTPStatus.GONE)
        self.assertEquals(response.json, dict())

    def test_returns_422_if_async_not_supported_but_required(self):
        self.broker.deprovision.side_effect = errors.ErrAsyncRequired()

        response: Response = self.client.delete(
            "/v2/service_instances/abc?service_id=service-id-here&plan_id=plan-id-here",
            headers={
                'X-Broker-Api-Version': '2.00'
            })

        self.assertEquals(response.status_code, http.HTTPStatus.UNPROCESSABLE_ENTITY)
        self.assertEquals(response.json, dict(
            error="AsyncRequired",
            description="This service plan requires client support for asynchronous service operations."
        ))