from unittest.mock import Mock, patch

from typer.testing import CliRunner

from torusdk.cli.misc import misc_app


class TestMiscCommands:
    def test_treasury_address_command(self):
        """Test the treasury-address command returns expected address format."""
        runner = CliRunner()

        # Mock the client and its method
        with patch("torusdk.cli.misc.make_custom_context") as mock_context:
            mock_client = Mock()
            mock_client.get_dao_treasury_address.return_value = (
                "5D4x123abc...treasury"
            )

            mock_ctx = Mock()
            mock_ctx.com_client.return_value = mock_client
            mock_ctx.progress_status.return_value.__enter__ = Mock()
            mock_ctx.progress_status.return_value.__exit__ = Mock()
            mock_ctx.output = Mock()

            mock_context.return_value = mock_ctx

            result = runner.invoke(misc_app, ["treasury-address"])

            assert result.exit_code == 0
            mock_client.get_dao_treasury_address.assert_called_once()
            mock_ctx.output.assert_called_once_with("5D4x123abc...treasury")

    def test_treasury_address_command_integration(self):
        """Integration test that verifies command structure without mocking client."""
        runner = CliRunner()

        # This will fail due to missing network connection, but we can verify
        # the command is properly registered and the structure is correct
        result = runner.invoke(misc_app, ["treasury-address", "--help"])

        assert result.exit_code == 0
        assert "treasury-address" in result.output
