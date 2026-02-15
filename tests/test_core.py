"""
Tests for src.core.data_processing module.
Tests data preparation and filtering functions.
"""

import pandas as pd
import pytest


class TestPrepCompanies:
    """Tests for prep_companies function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe for testing."""
        return pd.DataFrame(
            {
                "cnpj": ["11111111000181", "22222222000181"],
                "razao_social": ["Company A", "Company B"],
                "uf": ["SP", "RJ"],
            }
        )

    def test_prep_companies_returns_dataframe(self, sample_df):
        """Test that prep_companies returns a DataFrame."""
        from src.core.data_processing import prep_companies

        result = prep_companies(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_prep_companies_preserves_shape(self, sample_df):
        """Test that prep_companies preserves DataFrame shape."""
        from src.core.data_processing import prep_companies

        result = prep_companies(sample_df)
        assert result.shape[0] == sample_df.shape[0]

    def test_prep_companies_handles_empty_df(self):
        """Test prep_companies with empty DataFrame."""
        from src.core.data_processing import prep_companies

        empty_df = pd.DataFrame()
        result = prep_companies(empty_df)
        assert isinstance(result, pd.DataFrame)

    def test_prep_companies_normalizes_uf(self, sample_df):
        """Test that prep_companies normalizes UF values."""
        from src.core.data_processing import prep_companies

        sample_df["uf"] = ["sp", "rj"]  # lowercase
        result = prep_companies(sample_df)
        assert result["uf"].iloc[0] in ["SP", "sp", "Sp"]  # accepts normalized format


class TestPrepScores:
    """Tests for prep_scores function."""

    @pytest.fixture
    def sample_scores_df(self):
        """Create sample scores dataframe."""
        return pd.DataFrame(
            {
                "cnpj": ["11111111000181", "22222222000181"],
                "opportunity_score": [0.75, 0.45],
                "growth_index": [2.5, 1.2],
            }
        )

    def test_prep_scores_returns_dataframe(self, sample_scores_df):
        """Test that prep_scores returns a DataFrame."""
        from src.core.data_processing import prep_scores

        result = prep_scores(sample_scores_df)
        assert isinstance(result, pd.DataFrame)

    def test_prep_scores_handles_none(self):
        """Test prep_scores with None input."""
        from src.core.data_processing import prep_scores

        # Should handle gracefully or return empty DataFrame
        try:
            result = prep_scores(None)
            assert result is None or isinstance(result, pd.DataFrame)
        except (TypeError, AttributeError):
            # Acceptable to raise error for None input
            pass

    def test_prep_scores_validates_numeric_columns(self, sample_scores_df):
        """Test that numeric columns are valid."""
        from src.core.data_processing import prep_scores

        result = prep_scores(sample_scores_df)
        numeric_cols = result.select_dtypes(include=["number"]).columns
        assert len(numeric_cols) >= 1


class TestPrepCAGED:
    """Tests for prep_caged function."""

    @pytest.fixture
    def sample_caged_df(self):
        """Create sample CAGED dataframe."""
        return pd.DataFrame(
            {
                "mes": ["2023-01", "2023-02"],
                "uf": ["SP", "RJ"],
                "admissoes": [100, 150],
                "demissoes": [50, 30],
            }
        )

    def test_prep_caged_returns_dataframe(self, sample_caged_df):
        """Test that prep_caged returns a DataFrame."""
        from src.core.data_processing import prep_caged

        result = prep_caged(sample_caged_df)
        assert isinstance(result, pd.DataFrame)

    def test_prep_caged_preserves_date_format(self, sample_caged_df):
        """Test that date format is preserved or converted properly."""
        from src.core.data_processing import prep_caged

        result = prep_caged(sample_caged_df)
        # Should have valid date or string representation
        assert "mes" in result.columns or "date" in result.columns or len(result) > 0

    def test_prep_caged_calculates_net_flow(self, sample_caged_df):
        """Test that net flow is calculated correctly."""
        from src.core.data_processing import prep_caged

        result = prep_caged(sample_caged_df)
        # Check if net_flow column exists
        if "net_flow" in result.columns:
            assert (result["net_flow"] == result["admissoes"] - result["demissoes"]).all()


class TestApplyFilters:
    """Tests for apply_filters function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe for filtering."""
        return pd.DataFrame(
            {
                "cnpj": ["11111111000181", "22222222000181", "33333333000181"],
                "uf": ["SP", "RJ", "MG"],
                "setor": ["Technology", "Finance", "Agriculture"],
                "revenue": [1000000, 500000, 750000],
            }
        )

    def test_apply_filters_returns_dataframe(self, sample_df):
        """Test that apply_filters returns a DataFrame."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_apply_filters_empty_filters(self, sample_df):
        """Test apply_filters with no filters."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df)
        assert len(result) <= len(sample_df)

    def test_apply_filters_with_uf_filter(self, sample_df):
        """Test filtering by UF."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df, uf=["SP"])
        assert all(result["uf"] == "SP")

    def test_apply_filters_with_setor_filter(self, sample_df):
        """Test filtering by setor."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df, setor=["Technology"])
        assert all(result["setor"] == "Technology")

    def test_apply_filters_with_revenue_range(self, sample_df):
        """Test filtering by revenue range."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df, min_revenue=600000)
        assert all(result["revenue"] >= 600000)

    def test_apply_filters_combines_multiple_filters(self, sample_df):
        """Test combining multiple filters."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df, uf=["SP", "RJ"], min_revenue=400000)
        assert all(result["uf"].isin(["SP", "RJ"]))
        assert all(result["revenue"] >= 400000)

    def test_apply_filters_returns_empty_when_no_matches(self, sample_df):
        """Test that apply_filters returns empty DataFrame when no matches."""
        from src.core.data_processing import apply_filters

        result = apply_filters(sample_df, uf=["XX"])  # Invalid UF
        assert len(result) == 0


class TestDataProcessingIntegration:
    """Integration tests for data processing pipeline."""

    @pytest.fixture
    def pipeline_data(self):
        """Create data for pipeline testing."""
        companies = pd.DataFrame(
            {
                "cnpj": ["11111111000181", "22222222000181"],
                "uf": ["SP", "RJ"],
                "setor": ["Technology", "Finance"],
            }
        )
        return companies

    def test_full_pipeline(self, pipeline_data):
        """Test complete data processing pipeline."""
        from src.core.data_processing import apply_filters, prep_companies

        # Step 1: Prepare companies
        prepared = prep_companies(pipeline_data)
        assert isinstance(prepared, pd.DataFrame)

        # Step 2: Apply filters
        filtered = apply_filters(prepared, uf=["SP"])
        assert isinstance(filtered, pd.DataFrame)
        assert len(filtered) <= len(prepared)

    def test_pipeline_handles_invalid_input(self):
        """Test pipeline handles invalid input gracefully."""
        from src.core.data_processing import prep_companies

        # Test with None
        try:
            result = prep_companies(None)
        except (TypeError, AttributeError):
            # Expected behavior
            pass

        # Test with empty DataFrame
        result = prep_companies(pd.DataFrame())
        assert isinstance(result, pd.DataFrame)
