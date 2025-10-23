import pytest
from frame_check_core.util.col_similarity import jaro_winkler, zero_deps_jaro_winkler


@pytest.mark.parametrize(
    "s1, s2, expected",
    [
        # Exact matches - these should always return 1.0
        ("test", "test", 1.0),
        ("", "", 1.0),
        ("abc", "abc", 1.0),
        # Case insensitivity - should also be exact matches
        ("Test", "test", 1.0),
        ("ABC", "abc", 1.0),
        # Similar strings with high similarity
        ("color", "colour", 0.9666666666666667),
        ("first_name", "firstname", 0.98),
        ("phone_number", "phonenumber", 0.9833333333333333),
        # Moderate similarity
        ("customer", "customer_id", 0.9454545454545455),
        ("address", "addr", 0.9142857142857143),
        # Low similarity
        ("different", "strings", 0.4761904761904761),
        # Edge cases
        ("a", "a", 1.0),
        ("a", "b", 0.0),
        ("", "abc", 0.0),
    ],
)
def test_jaro_winkler(s1, s2, expected):
    """Test the jaro_winkler string similarity function."""
    result = jaro_winkler(s1, s2)
    assert result == pytest.approx(expected, rel=1e-10)


@pytest.mark.parametrize(
    "target_col, existing_cols, expected",
    [
        # Exact matches (should always match)
        ("name", ["name", "age", "address"], "name"),
        ("age", ["name", "age", "address"], "age"),
        # High similarity matches (above 0.9 threshold)
        ("first_name", ["firstname", "last_name", "address"], "firstname"),
        ("phone_number", ["phonenumber", "email", "address"], "phonenumber"),
        ("customer_id", ["customerid", "client_id", "id"], "customerid"),
        # Below threshold matches (should return None)
        ("age", ["income", "revenue", "amount"], None),
        ("phone", ["address", "email", "contact"], None),
        # Empty cases
        ("name", [], None),
        ("", ["name", "age"], None),
        # Case insensitive matches
        ("NAME", ["name", "age", "address"], "name"),
        ("Phone_Number", ["phone_number", "email"], "phone_number"),
        # Multiple potential matches (should return highest similarity)
        ("customer", ["customer_id", "customer_name", "cust"], "customer_id"),
        ("postal_code", ["postcode", "post_code", "zip"], "post_code"),
    ],
)
def test_zero_deps_jaro_winkler(target_col, existing_cols, expected):
    """Test the zero_deps_jaro_winkler function for finding similar columns."""
    result = zero_deps_jaro_winkler(target_col, existing_cols)
    assert result == expected
