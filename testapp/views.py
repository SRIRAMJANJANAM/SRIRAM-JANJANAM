from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from testapp.models import Contact, ChatMessage
import re
import json

# Home view
def home_view(request):
    return render(request, 'testapp/base.html')

# Contact form view
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        msg = request.POST.get('msg')
        Contact.objects.create(name=name, email=email, msg=msg)
        return redirect('/thanks')
    return render(request, 'testapp/contact.html')

# Skills view
def skill_view(request):
    return render(request, 'testapp/skills.html')

# Thank you page view
def thank_view(request):
    return render(request, 'testapp/thanks.html')

# About page view
def about_view(request):
    return render(request, 'testapp/about.html')

# --- Chatbot Logic ---

def chatbot_response(user_message):
    """Enhanced chatbot logic to ask for name and email after receiving phone number."""
    user_message = user_message.lower().strip()

    # Detect 10-digit phone number
    phone_match = re.search(r'\b\d{10}\b', user_message)
    if phone_match:
        return "Thanks! Can you also provide your name and email?"

    if any(word in user_message for word in ['hi', 'hello', 'hey', 'hola']):
        return "Hello! How can I help you today?"
    elif any(word in user_message for word in ['bye', 'goodbye', 'see you']):
        return "Goodbye! Thanks for visiting my portfolio."
    elif any(word in user_message for word in ['skill', 'what can you do', 'ability']):
        return "I'm a simple chatbot. You can ask me to say hello or goodbye!"
    elif any(word in user_message for word in ['name', 'who are you']):
        return "I'm the portfolio chatbot developed by Sri Ram❤"
    elif any(word in user_message for word in ['contact', 'meet']):
        return "You can contact through the Contact page or type your number."
    else:
        return "I'm still learning. Try asking me to say hello!"

@csrf_exempt
def chat_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            if not user_message:
                return JsonResponse({'response': "Please enter a message."})

            # Initialize session dict if not exists
            if 'chat_state' not in request.session:
                request.session['chat_state'] = {}

            state = request.session['chat_state']

            # STEP 1: Detect phone number
            phone_match = re.search(r'\b\d{10}\b', user_message)
            if phone_match and 'phone' not in state:
                state['phone'] = phone_match.group()
                request.session.modified = True
                return JsonResponse({'response': "Thanks! Can you please tell me your name?"})

            # STEP 2: Get name
            if 'phone' in state and 'name' not in state:
                state['name'] = user_message.title()
                request.session.modified = True
                return JsonResponse({'response': f"Thanks {state['name']}! Now, could you please provide your email?"})

            # STEP 3: Get email
            if 'phone' in state and 'name' in state and 'email' not in state:
                # Basic email validation
                if re.match(r"[^@]+@[^@]+\.[^@]+", user_message):
                    state['email'] = user_message
                    request.session.modified = True

                    # Save to database if you want
                    Contact.objects.create(
                        name=state['name'],
                        email=state['email'],
                        msg=f"Auto message from chatbot. Phone: {state['phone']}"
                    )

                    # Clear session after complete
                    summary = f"Thanks {state['name']}! I will contact you soon at {state['phone']} and {state['email']}."
                    request.session['chat_state'] = {}  # reset
                    return JsonResponse({'response': summary})
                else:
                    return JsonResponse({'response': "That doesn't look like a valid email. Please try again."})

            # Fallback
            return JsonResponse({'response': chatbot_response(user_message)})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
