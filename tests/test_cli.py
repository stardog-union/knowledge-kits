import os
import tempfile
from pathlib import Path

import yaml
from typer.testing import CliRunner

from stardog_union.kits.cli import kits

runner = CliRunner()


def test_init_creates_kit_structure():
    """Test that 'kits init' creates a valid kit structure with all expected files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            kits,
            [
                "init",
                "--name", "test-kit",
                "--group", "tutorial",
                "--version", "1.0",
                "--location", tmpdir,
            ],
        )

        # Assert command succeeded
        assert result.exit_code == 0
        assert "Kit initialized" in result.stdout

        # Assert kit.yaml was created
        kit_yaml_path = Path(tmpdir) / "kit.yaml"
        assert kit_yaml_path.exists()

        # Assert kit.yaml is valid and contains expected values
        with open(kit_yaml_path, "r") as f:
            kit_data = yaml.safe_load(f)
            assert kit_data["name"] == "test-kit"
            assert kit_data["group"] == "tutorial"
            assert kit_data["version"] == "1.0"

            # Verify default data structure
            assert "data" in kit_data
            assert len(kit_data["data"]) == 2
            assert kit_data["data"][0]["file"] == "data.ttl"
            assert kit_data["data"][0]["graph"] == "urn:data"
            assert kit_data["data"][1]["file"] == "schema.ttl"
            assert kit_data["data"][1]["graph"] == "urn:schema"

            # Verify default schema
            assert "schemas" in kit_data
            assert len(kit_data["schemas"]) == 1
            assert kit_data["schemas"][0]["name"] == "schema_name"
            assert kit_data["schemas"][0]["graphs"] == ["urn:schema"]

        # Assert readme.md was created
        readme_path = Path(tmpdir) / "readme.md"
        assert readme_path.exists()
        with open(readme_path, "r") as f:
            content = f.read()
            assert "tutorial:test-kit:1.0" in content

        # Assert data.ttl was created
        data_ttl_path = Path(tmpdir) / "data.ttl"
        assert data_ttl_path.exists()
        with open(data_ttl_path, "r") as f:
            content = f.read()
            assert "Data goes here" in content

        # Assert schema.ttl was created
        schema_ttl_path = Path(tmpdir) / "schema.ttl"
        assert schema_ttl_path.exists()
        with open(schema_ttl_path, "r") as f:
            content = f.read()
            assert "Schema goes here" in content


def test_init_uses_current_directory():
    """Test that 'kits init' uses current working directory when location is not specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            # Change to temp directory
            os.chdir(tmpdir)

            result = runner.invoke(
                kits,
                [
                    "init",
                    "--name", "my-kit",
                    "--group", "mygroup",
                    "--version", "2.0",
                ],
            )

            # Assert command succeeded
            assert result.exit_code == 0
            assert "Kit initialized" in result.stdout

            # Assert files were created in current directory
            kit_yaml_path = Path(tmpdir) / "kit.yaml"
            assert kit_yaml_path.exists()

            # Verify kit metadata
            with open(kit_yaml_path, "r") as f:
                kit_data = yaml.safe_load(f)
                assert kit_data["name"] == "my-kit"
                assert kit_data["group"] == "mygroup"
                assert kit_data["version"] == "2.0"

            # Verify other files exist
            assert (Path(tmpdir) / "readme.md").exists()
            assert (Path(tmpdir) / "data.ttl").exists()
            assert (Path(tmpdir) / "schema.ttl").exists()

        finally:
            os.chdir(original_cwd)
