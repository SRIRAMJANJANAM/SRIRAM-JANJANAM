from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
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

def chatbot_response(user_message, request):
    """Enhanced chatbot logic with page links and contextual responses."""
    user_message = user_message.lower().strip()

    # Generate absolute URLs for links
    base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
    
    # Define page URLs
    pages = {
        'home': base_url + '/',
        'skills': base_url + '/skills/',
        'contact': base_url + '/contact/',
        'about': base_url + '/about/',
        'thanks': base_url + '/thanks/'
    }

    # Detect 10-digit phone number
    phone_match = re.search(r'\b\d{10}\b', user_message)
    if phone_match:
        return {"response": "Thanks! Can you also provide your name and email?", "type": "text"}

    # Greetings
    if any(word in user_message for word in ['hi', 'hello', 'hey', 'hola']):
        return {"response": "Hello! Welcome to my portfolio. I can help you navigate through different sections. You can ask me about skills, contact information, about me, or other details!", "type": "text"}
    
    # Goodbyes
    elif any(word in user_message for word in ['bye', 'goodbye', 'see you']):
        return {"response": "Goodbye! Thanks for visiting my portfolio. Feel free to come back anytime!", "type": "text"}
    
    # Skills page
    elif any(word in user_message for word in ['skill', 'what can you do', 'ability', 'technologies', 'technology']):
        return {
            "response": "I can tell you about my technical skills and technologies I work with!",
            "type": "link",
            "link_text": "View My Skills",
            "link_url": pages['skills']
        }
    
    # Contact page
    elif any(word in user_message for word in ['contact', 'meet', 'reach', 'get in touch', 'email', 'phone']):
        return {
            "response": "You can contact me through the Contact page!",
            "type": "link", 
            "link_text": "Contact Me",
            "link_url": pages['contact']
        }
    
    # About page
    elif any(word in user_message for word in ['about', 'who are you', 'introduction', 'background']):
        return {
            "response": "Learn more about me on my About page:",
            "type": "link",
            "link_text": "About Me", 
            "link_url": pages['about']
        }
    
    # Home page
    elif any(word in user_message for word in ['home', 'main', 'portfolio', 'start']):
        return {
            "response": "Here's the link to my portfolio homepage:",
            "type": "link",
            "link_text": "Home",
            "link_url": pages['home']
        }
    
    # Thank you page
    elif any(word in user_message for word in ['thanks', 'thank you', 'appreciate']):
        return {
            "response": "You're welcome!",
            "type": "link",
            "link_text": "Thank You Page",
            "link_url": pages['thanks']
        }
    
    # Help - Return as HTML
    elif any(word in user_message for word in ['help', 'what can you do', 'options']):
        help_text = """
        I can help you with:<br>
        • <strong>Skills</strong> - View my technical skills and technologies<br>
        • <strong>Contact</strong> - Get in touch with me<br>  
        • <strong>About</strong> - Learn more about me<br>
        • <strong>Home</strong> - Go to the main portfolio page<br>
        • <strong>Phone registration</strong> - Share your phone number to get contacted<br><br>
        Just ask me about any of these topics!
        """
        return {"response": help_text, "type": "html"}
    
    # Name/identity
    elif any(word in user_message for word in ['name', 'who made you', 'developer']):
        return {"response": "I'm the portfolio chatbot developed by Sri Ram❤. I'm here to help you navigate through this portfolio website!", "type": "text"}
    
    # Default response
    else:
        return {"response": "I'm still learning. You can ask me about: skills, contact information, about me, or share your phone number to get contacted. Type 'help' for more options!", "type": "text"}


@csrf_exempt
def chat_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            if not user_message:
                return JsonResponse({'response': "Please enter a message.", "type": "text"})

            # Initialize session dict if not exists
            if 'chat_state' not in request.session:
                request.session['chat_state'] = {}

            state = request.session['chat_state']

            # STEP 1: Detect phone number
            phone_match = re.search(r'\b\d{10}\b', user_message)
            if phone_match and 'phone' not in state:
                state['phone'] = phone_match.group()
                request.session.modified = True
                return JsonResponse({'response': "Thanks! Can you please tell me your name?", "type": "text"})

            # STEP 2: Get name
            if 'phone' in state and 'name' not in state:
                state['name'] = user_message.title()
                request.session.modified = True
                return JsonResponse({'response': f"Thanks {state['name']}! Now, could you please provide your email?", "type": "text"})

            # STEP 3: Get email
            if 'phone' in state and 'name' in state and 'email' not in state:
                # Basic email validation
                if re.match(r"[^@]+@[^@]+\.[^@]+", user_message):
                    state['email'] = user_message
                    request.session.modified = True

                    # Save to database
                    Contact.objects.create(
                        name=state['name'],
                        email=state['email'],
                        msg=f"Auto message from chatbot. Phone: {state['phone']}"
                    )

                    # Clear session after complete
                    summary = f"Thanks {state['name']}! I will contact you soon at {state['phone']} and {state['email']}."
                    request.session['chat_state'] = {}  # reset
                    return JsonResponse({'response': summary, "type": "text"})
                else:
                    return JsonResponse({'response': "That doesn't look like a valid email. Please try again.", "type": "text"})

            # Fallback to enhanced chatbot response
            bot_response = chatbot_response(user_message, request)
            return JsonResponse(bot_response)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)