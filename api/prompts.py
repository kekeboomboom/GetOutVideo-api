"""
Prompt templates for AI processing styles.

This module contains the same refinement prompts as the original application,
providing various text processing styles for the API.
"""

text_refinement_prompts = {
    "Balanced and Detailed": """Turn the following unorganized text into a well-structured, readable format while retaining EVERY detail, context, and nuance of the original content.
    Refine the text to improve clarity, grammar, and coherence WITHOUT cutting, summarizing, or omitting any information.
    The goal is to make the content easier to read and process by:

    - Organizing the content into logical sections with appropriate subheadings.
    - Using bullet points or numbered lists where applicable to present facts, stats, or comparisons.
    - Highlighting key terms, names, or headings with bold text for emphasis.
    - Preserving the original tone, humor, and narrative style while ensuring readability.
    - Adding clear separators or headings for topic shifts to improve navigation.

    Ensure the text remains informative, capturing the original intent, tone,
    and details while presenting the information in a format optimized for analysis by both humans and AI.
    REMEMBER that Details are important, DO NOT overlook Any details, even small ones.
    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
    Format the entire response using Markdown syntax.
    Text:
    """,

    "Summary": """Summarize the following transcript into a concise and informative summary.
    Identify the core message, main arguments, and key pieces of information presented in the video.
    The summary should capture the essence of the video's content in a clear and easily understandable way.
    Aim for a summary that is shorter than the original transcript but still accurately reflects its key points.
    Focus on conveying the most important information and conclusions.
    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
    Format the entire response using Markdown syntax.
    Text: """,

    "Educational": """Transform the following transcript into a comprehensive educational text, resembling a textbook chapter. Structure the content with clear headings, subheadings, and bullet points to enhance readability and organization for educational purposes.

    Crucially, identify any technical terms, jargon, or concepts that are mentioned but not explicitly explained within the transcript. For each identified term, provide a concise definition (no more than two sentences) formatted as a blockquote.  Integrate these definitions strategically within the text, ideally near the first mention of the term, to enhance understanding without disrupting the flow.

    Ensure the text is highly informative, accurate, and retains all the original details and nuances of the transcript. The goal is to create a valuable educational resource that is easy to study and understand.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
    Format the entire response using Markdown syntax, including the blockquotes for definitions.

    Text:""",

    "Narrative Rewriting": """Rewrite the following transcript into an engaging narrative or story format. Transform the factual or conversational content into a more captivating and readable piece, similar to a short story or narrative article.

    While rewriting, maintain a close adherence to the original subjects and information presented in the video. Do not deviate significantly from the core topics or introduce unrelated elements.  The goal is to enhance engagement and readability through storytelling techniques without altering the fundamental content or message of the video.  Use narrative elements like descriptive language, scene-setting (if appropriate), and a compelling flow to make the information more accessible and enjoyable.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
    Format the entire response using Markdown syntax for appropriate emphasis or structure (like paragraph breaks).

    Text:""",

    "Q&A Generation": """Generate a set of questions and answers based on the following transcript for self-assessment or review.  For each question, create a corresponding answer.

    Format each question as a level 3 heading using Markdown syntax (### Question Text). Immediately following each question, provide the answer.  This format is designed for foldable sections, allowing users to easily hide and reveal answers for self-testing.

    Ensure the questions are relevant to the key information and concepts in the transcript and that the answers are accurate and comprehensive based on the video content.

    All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
    Format the entire response using Markdown syntax as specified.

    Text:"""
}


def get_available_styles():
    """Get list of available processing styles."""
    return list(text_refinement_prompts.keys())


def get_prompt_for_style(style_name: str) -> str:
    """
    Get the prompt template for a specific style.
    
    Args:
        style_name: Name of the processing style
        
    Returns:
        str: The prompt template
        
    Raises:
        ValueError: If style_name is not found
    """
    if style_name not in text_refinement_prompts:
        available = ", ".join(get_available_styles())
        raise ValueError(f"Unknown style '{style_name}'. Available styles: {available}")
    
    return text_refinement_prompts[style_name]