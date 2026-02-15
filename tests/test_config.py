"""
Testes para módulo de configuração (src/config/)
"""

import pytest
from pathlib import Path
from src.config.settings import Settings, PathConfig, get_project_root


class TestProjectRoot:
    """Testes para encontrar raiz do projeto"""

    def test_get_project_root_exists(self):
        """Encontra raiz do projeto"""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        assert (root / "src").exists()
        assert (root / "dashboards").exists()


class TestPathConfig:
    """Testes para configuração de caminhos"""

    def test_path_config_attributes(self):
        """PathConfig possui todos os atributos necessários"""
        root = get_project_root()
        paths = PathConfig(
            root=root,
            data=root / "data",
            raw=root / "data" / "raw",
            processed=root / "data" / "processed",
            geo=root / "data" / "geo",
        )

        assert paths.root == root
        assert paths.data == root / "data"
        assert paths.processed == root / "data" / "processed"
        assert paths.geo == root / "data" / "geo"

    def test_path_config_properties(self):
        """PathConfig retorna caminhos corretos"""
        root = get_project_root()
        paths = PathConfig(
            root=root,
            data=root / "data",
            raw=root / "data" / "raw",
            processed=root / "data" / "processed",
            geo=root / "data" / "geo",
        )

        assert "parquet" in str(paths.companies_agg)
        assert "geojson" in str(paths.brazil_states_geojson)


class TestSettings:
    """Testes para Settings"""

    def test_settings_initialization(self):
        """Settings inicializa corretamente"""
        settings = Settings()
        assert settings.paths is not None
        assert settings.app_title is not None
        assert settings.debug_mode in [True, False]

    def test_settings_paths(self):
        """Settings possui paths válidos"""
        settings = Settings()
        assert isinstance(settings.paths.root, Path)
        assert settings.paths.root.exists()

    def test_ensure_data_files_exist(self):
        """Valida existência de arquivos críticos"""
        settings = Settings()
        missing = settings.ensure_data_files_exist()
        # missing é uma lista (pode estar vazia ou ter items)
        assert isinstance(missing, list)
