
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_get_daily_theme():
    """Test that daily theme generation returns all required fields."""
    from lambda_function import get_daily_theme

    theme = get_daily_theme()

    assert 'day' in theme
    assert 'month' in theme
    assert 'season' in theme
    assert 'mood' in theme
    assert 'day_theme' in theme
    assert 'style' in theme
    assert 'date_str' in theme
    assert 'iteration' in theme

    # Verify season is valid
    assert theme['season'] in ['spring', 'summer', 'autumn', 'winter']

    # Verify day is valid
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    assert theme['day'] in valid_days

    print(f"✅ Theme generated: {theme}")


def test_lambda_handler_structure():
    """Test that lambda handler returns proper response structure."""
    with patch('lambda_function.bedrock_runtime') as mock_bedrock, \
         patch('lambda_function.s3_client') as mock_s3, \
         patch('lambda_function.dynamodb') as mock_dynamodb:

        # Mock Bedrock response
        mock_response = MagicMock()
        mock_response.__getitem__ = MagicMock(return_value=MagicMock())
        mock_response['body'].read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{'text': json.dumps({
                        'title': 'Test Poem',
                        'poem': 'This is a test poem\nWith multiple lines',
                        'inspiration': 'Testing'
                    })}]
                }
            }
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response

        # Mock DynamoDB
        mock_table = MagicMock()
        mock_table.scan.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table

        from lambda_function import lambda_handler

        event = {"source": "test"}
        context = MagicMock()

        result = lambda_handler(event, context)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'poem_title' in body
        assert 'date' in body

        print(f"✅ Lambda handler test passed: {body}")


if __name__ == '__main__':
    test_get_daily_theme()
    print("\n---\n")
    print("All basic tests passed! ✅")

