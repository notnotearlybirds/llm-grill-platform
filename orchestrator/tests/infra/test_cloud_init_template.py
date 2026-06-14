"""
Tests for infra/gpu-vm/cloud-init.tpl.yaml — the GPU VM cloud-config template.

cloud-init silently skips the whole runcmd block when one list item parses as
a YAML mapping instead of a string (e.g. an unquoted ": " inside a command),
leaving the VM idle with no runner, no callbacks and no fail-report. These
tests render the template the way `terraform templatefile` would and validate
the resulting document, so that class of bug is caught without spinning a VM.
"""

import re

import yaml

from src.infra.terraform import _TERRAFORM_DIR

_TEMPLATE = _TERRAFORM_DIR / "cloud-init.tpl.yaml"

# Realistic values: the docker image URI carries a ":" (tag) and the URL a
# "//", the two characters most likely to corrupt an unquoted YAML scalar.
_DUMMY_VALUE = "ghcr.io/llmgrill/llmgrill-runner-vllm:latest"
_DUMMY_SCENARIO = "model: dummy\nstages:\n  - users: 1"


def _render() -> str:
    """Emulate `terraform templatefile` on the cloud-init template.

    - `${indent(6, scenario_content)}` → an indented multi-line scenario
    - every other `${var}` → a dummy value containing a ":"
    - `$${` (terraform escape for shell vars) → literal `${`
    """
    rendered = _TEMPLATE.read_text()
    indented = ("\n" + " " * 6).join(_DUMMY_SCENARIO.splitlines())
    rendered = rendered.replace("${indent(6, scenario_content)}", indented)
    rendered = re.sub(r"(?<!\$)\$\{[^}]+\}", _DUMMY_VALUE, rendered)
    return rendered.replace("$${", "${")


class TestCloudInitTemplate:
    """The rendered template must stay a valid cloud-config document."""

    def test_should_render_to_valid_yaml(self):
        """
        Given: the template rendered with terraform-like substitutions
        When: parsed as YAML
        Then: it yields a mapping with the expected cloud-config sections
        """
        parsed = yaml.safe_load(_render())

        assert isinstance(parsed, dict)
        assert set(parsed) == {"write_files", "runcmd"}

    def test_should_keep_every_runcmd_item_a_string(self):
        """
        Given: the rendered template
        When: the runcmd block is parsed
        Then: every item is a plain string (an unquoted ": " inside a command
              would turn it into a dict and cc_runcmd would reject the block)
        """
        runcmd = yaml.safe_load(_render())["runcmd"]

        assert runcmd, "runcmd must not be empty"
        not_strings = [item for item in runcmd if not isinstance(item, str)]
        assert not_strings == []

    def test_should_give_every_write_file_a_path_and_content(self):
        """
        Given: the rendered template
        When: the write_files block is parsed
        Then: each entry carries a path and a non-empty string content
        """
        write_files = yaml.safe_load(_render())["write_files"]

        assert write_files, "write_files must not be empty"
        for entry in write_files:
            assert entry["path"].startswith("/")
            assert isinstance(entry["content"], str) and entry["content"].strip()
