"""
KIRAHT AI - Version 0.1
A beginner-friendly, terminal-based AI assistant powered by OpenAI.

Scope:
- Terminal text interaction only.
- In-memory conversation history for multi-turn context.
- Safe API key loading via .env (python-dotenv).
- Graceful error handling for missing keys, network issues, and API limits.
"""

import os
import sys
from dotenv import load_dotenv
import openai
from openai import OpenAI


def load_api_key() -> str:
    """
    Loads and validates the OpenAI API key from the .env file.
    Exits gracefully with helpful instructions if the key is missing or unchanged.
    """
    # Load environment variables from .env file
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    # Known placeholder values that indicate the user hasn't put their real key yet
    placeholders = {
        "your_openai_api_key_here",
        "your_api_key_here",
        "",
        None,
    }

    if not api_key or api_key.strip() in placeholders:
        print("\n[!] Configuration Error: OpenAI API key is missing or not configured.")
        print("    To fix this:")
        print("    1. Open the '.env' file in this folder.")
        print("    2. Replace the placeholder with your actual OpenAI API key:")
        print("       OPENAI_API_KEY=sk-proj-...")
        print("    3. Save the file and restart KIRAHT AI.\n")
        sys.exit(1)

    return api_key.strip()


def run_chat_loop(client: OpenAI) -> None:
    """
    Runs the interactive terminal chat loop with conversation history.
    """
    print("Type 'exit' to quit.")

    # Initialize conversation history with a helpful system prompt
    messages = [
        {
            "role": "system",
            "content": "You are KIRAHT AI, a helpful, polite, and concise AI assistant.",
        }
    ]

    while True:
        try:
            # Prompt user for input
            user_input = input("\nYou: ").strip()

            # Ignore empty inputs
            if not user_input:
                continue

            # Check for exit command (case-insensitive)
            if user_input.lower() in ("exit", "quit", "bye"):
                print("\nGoodbye!")
                break

            # Append the user's message to conversation history
            messages.append({"role": "user", "content": user_input})

            # Send the conversation history to the OpenAI Chat Completion API
            # gpt-4o-mini is fast, cost-effective, and highly capable
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )

                # Extract the assistant's reply text
                ai_response = response.choices[0].message.content or ""

                # Display the AI's response in the terminal
                print(f"\nkiraht AI: {ai_response}")

                # Save the assistant's response to history to remember previous context
                messages.append({"role": "assistant", "content": ai_response})

            except openai.AuthenticationError:
                # Remove the unanswered user message so conversation state stays consistent
                messages.pop()
                print("\nkiraht AI: [Authentication Error] Invalid API key. Please verify the key in your .env file.")

            except openai.RateLimitError:
                messages.pop()
                print("\nkiraht AI: [Rate Limit Error] OpenAI quota or rate limit exceeded. Please check your account usage.")

            except openai.APIConnectionError:
                messages.pop()
                print("\nkiraht AI: [Connection Error] Unable to connect to OpenAI servers. Please check your internet connection.")

            except openai.APIStatusError as err:
                messages.pop()
                print(f"\nkiraht AI: [API Error {err.status_code}] An error occurred while communicating with the model.")

            except Exception:
                messages.pop()
                print("\nkiraht AI: [Error] An unexpected error occurred. Please try again.")

        except (KeyboardInterrupt, EOFError):
            # Gracefully handle Ctrl+C or Ctrl+D/Z
            print("\nGoodbye!")
            break


def main() -> None:
    """
    Main entry point for KIRAHT AI V0.1.
    """
    # 1. Load and validate API key
    api_key = load_api_key()

    # 2. Initialize the official OpenAI client
    client = OpenAI(api_key=api_key)

    # 3. Start the interactive chat loop
    run_chat_loop(client)


if __name__ == "__main__":
    main()
