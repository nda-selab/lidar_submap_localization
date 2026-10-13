from pathlib import Path
import xml.etree.ElementTree as ET


def test_package_xml():
    package = Path(__file__).resolve().parents[1]
    tree = ET.parse(package / 'package.xml')
    assert tree.getroot().findtext('name') == 'lidar_submap_localization'


def test_config():
    import yaml
    package = Path(__file__).resolve().parents[1]
    params = yaml.safe_load((package / 'config/localization.yaml').read_text())['submap_localizer']['ros__parameters']
    assert params['cloud_topic'] == '/cloud_registered'
    assert params['odom_topic'] == '/odom_nav'
    assert params['map_frame'] != params['odom_frame']
    assert params['max_alignment_age_sec'] > params['submap_duration_sec'] / 2
    assert params['bootstrap_max_correction_translation'] >= params['max_correction_translation']
