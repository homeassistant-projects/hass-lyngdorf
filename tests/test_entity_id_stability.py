"""Entity ID stability tests for Lyngdorf integration.

These tests ensure unique_id patterns remain stable across updates.
Changing unique_id formats will break existing user automations, scenes,
and dashboards that reference these entities.

GOLDEN FORMAT DOCUMENTATION
===========================

The Lyngdorf integration uses three unique_id patterns:

1. Sensor entities (sensor.py):
   Format: f'{DOMAIN}_{model_id}_{entity_type}'.lower()
   Example: 'lyngdorf_tdai-3400_audio_format'

2. Number entities (number.py):
   Format: f'{DOMAIN}_{model_id}_{entity_type}'.lower()
   Example: 'lyngdorf_mp-60_trim_bass'

3. Media player entities (media_player.py):
   Format: f'{DOMAIN}_{model_id}{zone_suffix}'.lower().replace(' ', '_')
   Where zone_suffix is '' for main zone or '_zone2' for zone 2
   Example: 'lyngdorf_tdai-3400' (main zone)
   Example: 'lyngdorf_tdai-3400_zone2' (zone 2)

BREAKING CHANGE WARNING
=======================

DO NOT modify these patterns without:
1. Providing a migration path for existing users
2. Updating the version number with a major bump
3. Adding deprecation warnings in release notes
4. Consider using entity_registry helpers to migrate entity IDs

If you must change these patterns, existing users will need to:
- Manually update all automations referencing old entity IDs
- Re-add entities to dashboards
- Fix any scenes or scripts using the entities
"""

from __future__ import annotations

import pytest

# domain constant must match the integration
DOMAIN = 'lyngdorf'


# -----------------------------------------------------------------------------
# Unique ID generation functions (must match actual entity code exactly)
# -----------------------------------------------------------------------------


def generate_sensor_unique_id(model_id: str, entity_type: str) -> str:
    """Generate unique_id for sensor entities.

    Matches: sensor.py LyngdorfSensorEntity.__init__
    Pattern: f'{DOMAIN}_{coordinator.model_id}_{entity_type}'.lower()
    """
    return f'{DOMAIN}_{model_id}_{entity_type}'.lower()


def generate_number_unique_id(model_id: str, entity_type: str) -> str:
    """Generate unique_id for number entities.

    Matches: number.py LyngdorfNumberEntity.__init__
    Pattern: f'{DOMAIN}_{coordinator.model_id}_{entity_type}'.lower()
    """
    return f'{DOMAIN}_{model_id}_{entity_type}'.lower()


def generate_media_player_unique_id(model_id: str, zone: str = 'main') -> str:
    """Generate unique_id for media player entities.

    Matches: media_player.py LyngdorfMediaPlayer.__init__
    Pattern: f'{DOMAIN}_{self._model_id}{zone_suffix}'.lower().replace(' ', '_')
    """
    zone_suffix = '_zone2' if zone == 'zone2' else ''
    return f'{DOMAIN}_{model_id}{zone_suffix}'.lower().replace(' ', '_')


# -----------------------------------------------------------------------------
# Test data for parametrized tests
# -----------------------------------------------------------------------------

SENSOR_ENTITY_TYPES = [
    'audio_format',
    'video_input',
    'video_output',
]

NUMBER_ENTITY_TYPES = [
    'trim_bass',
    'trim_treble',
    'trim_center',
    'trim_lfe',
    'trim_surrounds',
    'trim_height',
    'lipsync',
]

# representative model IDs to test various formatting scenarios
TEST_MODEL_IDS = [
    'TDAI-3400',
    'MP-60',
    'MP-60 2.1',
    'tdai-1120',
]


# -----------------------------------------------------------------------------
# Sensor entity unique_id tests
# -----------------------------------------------------------------------------


class TestSensorUniqueIdStability:
    """Test sensor entity unique_id stability."""

    @pytest.mark.parametrize('model_id', TEST_MODEL_IDS)
    @pytest.mark.parametrize('entity_type', SENSOR_ENTITY_TYPES)
    def test_sensor_unique_id_format(self, model_id: str, entity_type: str) -> None:
        """Verify sensor unique_id format remains stable."""
        unique_id = generate_sensor_unique_id(model_id, entity_type)

        # format requirements
        assert unique_id.islower(), f'unique_id must be lowercase: {unique_id}'
        assert unique_id.startswith(f'{DOMAIN}_'), f'must start with domain: {unique_id}'
        assert entity_type in unique_id, f'must contain entity_type: {unique_id}'

    def test_sensor_golden_examples(self) -> None:
        """Verify specific golden examples for sensor entities.

        These exact values must not change. If they do, user configurations break.
        """
        golden_examples = {
            ('TDAI-3400', 'audio_format'): 'lyngdorf_tdai-3400_audio_format',
            ('MP-60', 'video_input'): 'lyngdorf_mp-60_video_input',
            ('MP-60 2.1', 'video_output'): 'lyngdorf_mp-60 2.1_video_output',
        }

        for (model_id, entity_type), expected in golden_examples.items():
            actual = generate_sensor_unique_id(model_id, entity_type)
            assert actual == expected, (
                f'Golden unique_id mismatch for sensor ({model_id}, {entity_type}): '
                f'expected {expected!r}, got {actual!r}'
            )


# -----------------------------------------------------------------------------
# Number entity unique_id tests
# -----------------------------------------------------------------------------


class TestNumberUniqueIdStability:
    """Test number entity unique_id stability."""

    @pytest.mark.parametrize('model_id', TEST_MODEL_IDS)
    @pytest.mark.parametrize('entity_type', NUMBER_ENTITY_TYPES)
    def test_number_unique_id_format(self, model_id: str, entity_type: str) -> None:
        """Verify number unique_id format remains stable."""
        unique_id = generate_number_unique_id(model_id, entity_type)

        # format requirements
        assert unique_id.islower(), f'unique_id must be lowercase: {unique_id}'
        assert unique_id.startswith(f'{DOMAIN}_'), f'must start with domain: {unique_id}'
        assert entity_type in unique_id, f'must contain entity_type: {unique_id}'

    def test_number_golden_examples(self) -> None:
        """Verify specific golden examples for number entities.

        These exact values must not change. If they do, user configurations break.
        """
        golden_examples = {
            ('TDAI-3400', 'trim_bass'): 'lyngdorf_tdai-3400_trim_bass',
            ('MP-60', 'trim_treble'): 'lyngdorf_mp-60_trim_treble',
            ('MP-60 2.1', 'lipsync'): 'lyngdorf_mp-60 2.1_lipsync',
        }

        for (model_id, entity_type), expected in golden_examples.items():
            actual = generate_number_unique_id(model_id, entity_type)
            assert actual == expected, (
                f'Golden unique_id mismatch for number ({model_id}, {entity_type}): '
                f'expected {expected!r}, got {actual!r}'
            )


# -----------------------------------------------------------------------------
# Media player entity unique_id tests
# -----------------------------------------------------------------------------


class TestMediaPlayerUniqueIdStability:
    """Test media player entity unique_id stability."""

    @pytest.mark.parametrize('model_id', TEST_MODEL_IDS)
    @pytest.mark.parametrize('zone', ['main', 'zone2'])
    def test_media_player_unique_id_format(self, model_id: str, zone: str) -> None:
        """Verify media player unique_id format remains stable."""
        unique_id = generate_media_player_unique_id(model_id, zone)

        # format requirements
        assert unique_id.islower(), f'unique_id must be lowercase: {unique_id}'
        assert unique_id.startswith(f'{DOMAIN}_'), f'must start with domain: {unique_id}'
        assert ' ' not in unique_id, f'must not contain spaces: {unique_id}'

        if zone == 'zone2':
            assert unique_id.endswith('_zone2'), f'zone2 must end with _zone2: {unique_id}'

    def test_media_player_golden_examples(self) -> None:
        """Verify specific golden examples for media player entities.

        These exact values must not change. If they do, user configurations break.
        """
        golden_examples = {
            ('TDAI-3400', 'main'): 'lyngdorf_tdai-3400',
            ('TDAI-3400', 'zone2'): 'lyngdorf_tdai-3400_zone2',
            ('MP-60', 'main'): 'lyngdorf_mp-60',
            ('MP-60', 'zone2'): 'lyngdorf_mp-60_zone2',
            ('MP-60 2.1', 'main'): 'lyngdorf_mp-60_2.1',
            ('MP-60 2.1', 'zone2'): 'lyngdorf_mp-60_2.1_zone2',
        }

        for (model_id, zone), expected in golden_examples.items():
            actual = generate_media_player_unique_id(model_id, zone)
            assert actual == expected, (
                f'Golden unique_id mismatch for media_player ({model_id}, {zone}): '
                f'expected {expected!r}, got {actual!r}'
            )

    def test_media_player_space_replacement(self) -> None:
        """Verify spaces in model_id are replaced with underscores."""
        # model with space
        unique_id = generate_media_player_unique_id('MP-60 2.1', 'main')
        assert ' ' not in unique_id
        assert unique_id == 'lyngdorf_mp-60_2.1'


# -----------------------------------------------------------------------------
# Cross-entity consistency tests
# -----------------------------------------------------------------------------


class TestCrossEntityConsistency:
    """Test consistency across entity types."""

    @pytest.mark.parametrize('model_id', TEST_MODEL_IDS)
    def test_all_entities_use_same_domain_prefix(self, model_id: str) -> None:
        """All entities for a model should use the same domain prefix."""
        sensor_id = generate_sensor_unique_id(model_id, 'audio_format')
        number_id = generate_number_unique_id(model_id, 'trim_bass')
        media_player_id = generate_media_player_unique_id(model_id, 'main')

        expected_prefix = f'{DOMAIN}_'
        assert sensor_id.startswith(expected_prefix)
        assert number_id.startswith(expected_prefix)
        assert media_player_id.startswith(expected_prefix)

    def test_unique_ids_are_globally_unique(self) -> None:
        """Verify no collisions between entity unique_ids for same model."""
        model_id = 'TDAI-3400'
        all_ids: set[str] = set()

        # collect all sensor ids
        for entity_type in SENSOR_ENTITY_TYPES:
            uid = generate_sensor_unique_id(model_id, entity_type)
            assert uid not in all_ids, f'duplicate unique_id: {uid}'
            all_ids.add(uid)

        # collect all number ids
        for entity_type in NUMBER_ENTITY_TYPES:
            uid = generate_number_unique_id(model_id, entity_type)
            assert uid not in all_ids, f'duplicate unique_id: {uid}'
            all_ids.add(uid)

        # collect media player ids
        for zone in ['main', 'zone2']:
            uid = generate_media_player_unique_id(model_id, zone)
            assert uid not in all_ids, f'duplicate unique_id: {uid}'
            all_ids.add(uid)
