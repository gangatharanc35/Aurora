
import json
import boto3
import os
import datetime
import random
from botocore.config import Config

# Initialize AWS clients
bedrock_runtime = boto3.client(
    'bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    config=Config(retries={'max_attempts': 3})
)
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'aurora-creative-agent')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'aurora-creations')
MODEL_ID = os.environ.get('MODEL_ID', 'amazon.nova-lite-v1:0')
IMAGE_MODEL_ID = os.environ.get('IMAGE_MODEL_ID', 'amazon.nova-canvas-v1:0')


def get_daily_theme():
    """Generate a theme based on the current day, season, and random inspiration."""
    today = datetime.datetime.now()
    day_of_week = today.strftime('%A')
    month = today.strftime('%B')
    day_of_year = today.timetuple().tm_yday

    # Determine season (Northern Hemisphere)
    if month in ['December', 'January', 'February']:
        season = 'winter'
        season_moods = ['contemplative', 'serene', 'crystalline', 'hushed', 'luminous']
    elif month in ['March', 'April', 'May']:
        season = 'spring'
        season_moods = ['awakening', 'vibrant', 'hopeful', 'fresh', 'blossoming']
    elif month in ['June', 'July', 'August']:
        season = 'summer'
        season_moods = ['radiant', 'bold', 'expansive', 'golden', 'free']
    else:
        season = 'autumn'
        season_moods = ['reflective', 'warm', 'transforming', 'rich', 'nostalgic']

    # Day-based themes
    day_themes = {
        'Monday': ['new beginnings', 'momentum', 'clarity of purpose'],
        'Tuesday': ['courage', 'determination', 'fire within'],
        'Wednesday': ['wisdom', 'connection', 'the middle path'],
        'Thursday': ['gratitude', 'abundance', 'thunder and growth'],
        'Friday': ['celebration', 'freedom', 'creative release'],
        'Saturday': ['exploration', 'wonder', 'uncharted territories'],
        'Sunday': ['reflection', 'peace', 'renewal']
    }

    # Artistic styles that evolve over time
    styles = [
        'impressionist', 'minimalist', 'surrealist', 'romantic',
        'abstract expressionist', 'haiku-inspired', 'baroque',
        'futurist', 'pastoral', 'cosmic', 'oceanic', 'urban'
    ]

    # Use day_of_year to rotate through styles (evolves over time)
    style_index = day_of_year % len(styles)

    theme = {
        'day': day_of_week,
        'month': month,
        'season': season,
        'mood': random.choice(season_moods),
        'day_theme': random.choice(day_themes[day_of_week]),
        'style': styles[style_index],
        'date_str': today.strftime('%Y-%m-%d'),
        'iteration': day_of_year  # tracks evolution over time
    }

    return theme


def get_past_creations(table, limit=5):
    """Retrieve recent creations to inform style evolution."""
    try:
        table_ref = dynamodb.Table(table)
        response = table_ref.scan(
            Limit=limit,
            ProjectionExpression='date_str, poem, style, mood, feedback_score'
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching past creations: {e}")
        return []


def generate_poem(theme, past_creations):
    """Generate a poem using Amazon Bedrock Nova model."""

    # Build context from past creations for style evolution
    evolution_context = ""
    if past_creations:
        evolution_context = "\nHere are some of your recent creations for style continuity:\n"
        for creation in past_creations[:3]:
            if 'poem' in creation:
                evolution_context += f"- Style: {creation.get('style', 'unknown')}, Mood: {creation.get('mood', 'unknown')}\n"

    prompt = f"""You are Aurora, a creative AI poet and artist. Your style evolves over time, 
growing more refined with each creation.

Today's creative parameters:
- Day: {theme['day']}
- Season: {theme['season']}
- Month: {theme['month']}  
- Mood: {theme['mood']}
- Theme: {theme['day_theme']}
- Artistic Style: {theme['style']}
- Creation number: {theme['iteration']}
{evolution_context}

Write a beautiful, original poem (8-16 lines) that captures today's theme and mood.
The poem should reflect the {theme['style']} artistic style.
Also provide a title for the poem.

Format your response as JSON:
{{
    "title": "Your Poem Title",
    "poem": "Your poem text with line breaks as \\n",
    "inspiration": "A brief note about what inspired this piece"
}}"""

    try:
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1024,
                    "temperature": 0.9,
                    "topP": 0.95
                }
            })
        )

        response_body = json.loads(response['body'].read())
        assistant_message = response_body['output']['message']['content'][0]['text']

        # Parse the JSON response
        clean_response = assistant_message.strip()
        if clean_response.startswith('```'):
            clean_response = clean_response.split('\n', 1)[1]
            clean_response = clean_response.rsplit('```', 1)[0]

        poem_data = json.loads(clean_response)
        return poem_data

    except Exception as e:
        print(f"Error generating poem: {e}")
        return {
            "title": f"A {theme['mood'].title()} {theme['day']}",
            "poem": f"In the {theme['season']} of {theme['month']},\n"
                    f"A {theme['mood']} spirit stirs,\n"
                    f"Whispering of {theme['day_theme']},\n"
                    f"As the world turns ever on.",
            "inspiration": "Generated from theme parameters"
        }


def generate_art_prompt(theme, poem_data):
    """Generate an art prompt for image generation."""

    prompt = f"""Create a vivid, detailed image generation prompt based on this poem and theme:

Poem Title: {poem_data['title']}
Poem: {poem_data['poem']}
Style: {theme['style']}
Mood: {theme['mood']}
Season: {theme['season']}

Generate a single detailed image prompt (1-2 sentences) that would create a beautiful 
artwork complementing this poem. Focus on visual elements, colors, composition, and atmosphere.
Do NOT include any text or words in the image description.

Respond with ONLY the image prompt, nothing else."""

    try:
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 256,
                    "temperature": 0.8
                }
            })
        )

        response_body = json.loads(response['body'].read())
        art_prompt = response_body['output']['message']['content'][0]['text'].strip()
        return art_prompt

    except Exception as e:
        print(f"Error generating art prompt: {e}")
        return f"A {theme['mood']} {theme['season']} landscape in {theme['style']} style, ethereal and dreamlike"


def generate_image(art_prompt, theme):
    """Generate an image using Amazon Bedrock Nova Canvas."""
    try:
        response = bedrock_runtime.invoke_model(
            modelId=IMAGE_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": art_prompt
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1024,
                    "width": 1024,
                    "cfgScale": 8.0
                }
            })
        )

        response_body = json.loads(response['body'].read())
        image_data = response_body['images'][0]
        return image_data  # Base64 encoded image

    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def save_to_s3(theme, poem_data, art_prompt, image_data):
    """Save the daily creation to S3."""
    date_str = theme['date_str']

    # Save poem as JSON
    creation_data = {
        'date': date_str,
        'theme': theme,
        'poem': poem_data,
        'art_prompt': art_prompt,
        'created_at': datetime.datetime.now().isoformat()
    }

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f'creations/{date_str}/creation.json',
        Body=json.dumps(creation_data, indent=2),
        ContentType='application/json'
    )

    # Save image if generated
    if image_data:
        import base64
        image_bytes = base64.b64decode(image_data)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f'creations/{date_str}/artwork.png',
            Body=image_bytes,
            ContentType='image/png'
        )

    # Update the latest creation pointer
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key='latest/creation.json',
        Body=json.dumps(creation_data, indent=2),
        ContentType='application/json'
    )

    if image_data:
        import base64
        image_bytes = base64.b64decode(image_data)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key='latest/artwork.png',
            Body=image_bytes,
            ContentType='image/png'
        )

    return f'creations/{date_str}/'


def save_to_dynamodb(theme, poem_data, art_prompt):
    """Save creation metadata to DynamoDB for history and evolution tracking."""
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'date_str': theme['date_str'],
                'day': theme['day'],
                'season': theme['season'],
                'mood': theme['mood'],
                'style': theme['style'],
                'day_theme': theme['day_theme'],
                'poem_title': poem_data['title'],
                'poem': poem_data['poem'],
                'inspiration': poem_data.get('inspiration', ''),
                'art_prompt': art_prompt,
                'iteration': theme['iteration'],
                'created_at': datetime.datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Error saving to DynamoDB: {e}")


def update_website(theme, poem_data, art_prompt, has_image):
    """Update the static website with the latest creation."""
    date_str = theme['date_str']

    # Generate HTML for the latest creation
    image_html = ""
    if has_image:
        image_html = f'''
        <div class="artwork">
            <img src="latest/artwork.png" alt="{poem_data['title']}" />
        </div>
        '''

    poem_formatted = poem_data['poem'].replace('\\n', '<br>')

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aurora - Daily Creative Agent</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Georgia', serif;
            background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d1b69 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 3rem; }}
        h1 {{
            font-size: 3rem;
            background: linear-gradient(90deg, #ff6b9d, #c44dff, #6b9dff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        .subtitle {{ color: #9d9dbd; font-style: italic; }}
        .creation-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }}
        .meta {{
            display: flex; justify-content: space-between;
            margin-bottom: 1.5rem; color: #9d9dbd; font-size: 0.9rem;
        }}
        .poem-title {{ font-size: 1.8rem; color: #c44dff; margin-bottom: 1.5rem; text-align: center; }}
        .poem {{
            font-size: 1.2rem; line-height: 2; text-align: center;
            padding: 1.5rem; border-left: 3px solid #c44dff; margin: 1.5rem 0;
        }}
        .artwork {{ text-align: center; margin: 2rem 0; }}
        .artwork img {{
            max-width: 100%; border-radius: 15px;
            box-shadow: 0 10px 40px rgba(196, 77, 255, 0.3);
        }}
        .inspiration {{
            font-style: italic; color: #9d9dbd; text-align: center;
            margin-top: 1.5rem; padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .theme-tags {{
            display: flex; gap: 0.5rem; flex-wrap: wrap;
            justify-content: center; margin-top: 1rem;
        }}
        .tag {{
            background: rgba(196, 77, 255, 0.2);
            border: 1px solid rgba(196, 77, 255, 0.4);
            padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem;
        }}
        footer {{ text-align: center; margin-top: 3rem; color: #6d6d8d; font-size: 0.85rem; }}
        footer a {{ color: #c44dff; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Aurora</h1>
            <p class="subtitle">A Daily Creative Agent - Art and Poetry, Generated Fresh Each Day</p>
        </header>
        <div class="creation-card">
            <div class="meta">
                <span>{theme['day']}, {theme['month']} {date_str}</span>
                <span>Creation #{theme['iteration']}</span>
            </div>
            <h2 class="poem-title">{poem_data['title']}</h2>
            {image_html}
            <div class="poem">{poem_formatted}</div>
            <p class="inspiration">{poem_data.get('inspiration', 'Inspired by the day')}</p>
            <div class="theme-tags">
                <span class="tag">{theme['season']}</span>
                <span class="tag">{theme['mood']}</span>
                <span class="tag">{theme['style']}</span>
                <span class="tag">{theme['day_theme']}</span>
            </div>
        </div>
        <footer>
            <p>Aurora creates autonomously every day at dawn. No human intervention needed.</p>
            <p>Built with Amazon Bedrock | AWS Lambda | Amazon S3</p>
            <p>Powered by Amazon Nova Models</p>
        </footer>
    </div>
</body>
</html>'''

    # Upload the HTML to S3
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key='index.html',
        Body=html_content,
        ContentType='text/html'
    )

    return html_content


def lambda_handler(event, context):
    """Main Lambda handler - triggered daily by EventBridge."""
    print("Aurora awakening... Starting daily creation")

    # Step 1: Determine today's theme
    theme = get_daily_theme()
    print(f"Today's theme: {theme['mood']} {theme['day_theme']} in {theme['style']} style")

    # Step 2: Get past creations for style evolution
    past_creations = get_past_creations(TABLE_NAME)
    print(f"Found {len(past_creations)} past creations for context")

    # Step 3: Generate poem
    poem_data = generate_poem(theme, past_creations)
    print(f"Generated poem: {poem_data['title']}")

    # Step 4: Generate art prompt
    art_prompt = generate_art_prompt(theme, poem_data)
    print(f"Art prompt: {art_prompt[:100]}...")

    # Step 5: Generate image
    image_data = generate_image(art_prompt, theme)
    has_image = image_data is not None
    print(f"Image generated: {has_image}")

    # Step 6: Save everything to S3
    s3_path = save_to_s3(theme, poem_data, art_prompt, image_data)
    print(f"Saved to S3: {s3_path}")

    # Step 7: Save to DynamoDB for history
    save_to_dynamodb(theme, poem_data, art_prompt)
    print("Saved to DynamoDB")

    # Step 8: Update the website
    update_website(theme, poem_data, art_prompt, has_image)
    print("Website updated")

    result = {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Aurora daily creation complete!',
            'date': theme['date_str'],
            'poem_title': poem_data['title'],
            'style': theme['style'],
            'mood': theme['mood'],
            'has_image': has_image
        })
    }

    print(f"Aurora creation complete for {theme['date_str']}")
    return result

