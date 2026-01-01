# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.exceptions import ValidationError
from testapp.models import Contact, ChatMessage, Experience
import re
import json
import datetime
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

def send_contact_emails(name, email, message, phone=None, source="Contact Form", request=None):
    """
    Reusable function to send emails for both contact form and chatbot
    Returns: tuple (success, error_message)
    """
    YOUR_EMAIL = "sriramjanjanam13@gmail.com" 
    if request:
        base_url = request.build_absolute_uri('/')[:-1]
    else:
        base_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
    
    current_time = datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    # ========== 1. ADMIN EMAIL (TO YOU) ==========
    admin_subject = f"📨 New {source}: {name}"
    
    admin_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #67d2c8 0%, #3a0ca3 100%); color: white; padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef; }}
            .info-box {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .label {{ font-weight: bold; color: #3a0ca3; min-width: 120px; display: inline-block; }}
            .actions {{ background: #e7f3ff; padding: 20px; border-radius: 8px; margin-top: 25px; text-align: center; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
            .btn {{ display: inline-block; padding: 12px 25px; background: #67d2c8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px; }}
            .source-badge {{ background: #f0f9ff; padding: 5px 15px; border-radius: 20px; font-size: 12px; color: #3a0ca3; display: inline-block; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">📨 New Message Received!</h1>
                <p style="margin: 10px 0 0; opacity: 0.9;">From your portfolio website</p>
            </div>
            
            <div class="content">
                <div class="source-badge">
                    <strong>Source:</strong> {source}
                </div>
                
                <h2 style="color: #3a0ca3; margin-top: 0;">👤 Contact Details</h2>
                
                <div class="info-box">
                    <div><span class="label">Name:</span> <strong>{name}</strong></div>
                    <div><span class="label">Email:</span> <a href="mailto:{email}" style="color: #3a0ca3;">{email}</a></div>
                    <div><span class="label">Phone:</span> {phone if phone else 'Not provided'}</div>
                    <div><span class="label">Time:</span> {current_time}</div>
                </div>
                
                <h3 style="color: #3a0ca3;">💬 Message</h3>
                <div class="info-box">
                    <p style="margin: 0; white-space: pre-line;">{message}</p>
                </div>
                
                <div class="actions">
                    <h3 style="margin-top: 0; color: #3a0ca3;">🎯 Quick Actions</h3>
                    <a href="mailto:{email}" class="btn">📧 Reply to {name}</a>
                    {f'<a href="tel:{phone}" class="btn">📞 Call {name}</a>' if phone else ''}
                    <br><br>
                    <a href="{base_url}/admin/testapp/contact/" style="color: #67d2c8; text-decoration: underline;">
                        View in Admin Panel
                    </a>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from your portfolio website.</p>
                    <p>© {datetime.datetime.now().year} Sri Ram Portfolio</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    admin_plain = f"""NEW {source.upper()} SUBMISSION

Name: {name}
Email: {email}
Phone: {phone if phone else 'Not provided'}
Time: {current_time}
Source: {source}

Message:
{message}

Reply to: {email}
{f'Call: {phone}' if phone else ''}
"""
    
    # ========== 2. USER EMAIL (CONFIRMATION) ==========
    user_subject = f"✅ Thank you for contacting Sri Ram Janjanam!"
    
    user_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #67d2c8 0%, #3a0ca3 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef; }}
            .success-icon {{ text-align: center; margin: 20px 0; }}
            .check-icon {{ font-size: 60px; color: #10b981; }}
            .message-box {{ background: white; padding: 25px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #67d2c8; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
            .highlight {{ color: #3a0ca3; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 28px;">✅ Message Received!</h1>
                <p style="margin: 10px 0 0; opacity: 0.9;">Thank you for reaching out</p>
            </div>
            
            <div class="content">
                <div class="success-icon">
                    <div class="check-icon">✓</div>
                </div>
                
                <h2 style="color: #3a0ca3; text-align: center;">Hello {name},</h2>
                
                <div class="message-box">
                    <p style="margin: 0 0 15px;">Thank you for contacting <span class="highlight">Sri Ram Janjanam</span> through his portfolio website!</p>
                    
                    <p style="margin: 15px 0;"><strong>✅ Your message has been received successfully.</strong></p>
                    
                    <div style="background: #f0f9ff; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>📋 Your Submission:</strong></p>
                        <p style="margin: 5px 0;">• <strong>Name:</strong> {name}</p>
                        <p style="margin: 5px 0;">• <strong>Email:</strong> {email}</p>
                        {f'<p style="margin: 5px 0;">• <strong>Phone:</strong> {phone}</p>' if phone else ''}
                        <p style="margin: 5px 0;">• <strong>Date:</strong> {datetime.datetime.now().strftime("%B %d, %Y")}</p>
                    </div>
                    
                    <h3 style="color: #3a0ca3; margin-top: 25px;">⏳ What happens next?</h3>
                    <ol style="margin: 15px 0; padding-left: 20px;">
                        <li>Sri Ram will review your message within <strong>24-48 hours</strong></li>
                        <li>You'll receive a personalized response at <strong>{email}</strong></li>
                        <li>For urgent matters, connect via LinkedIn</li>
                    </ol>
                </div>
                
                <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; margin-top: 25px;">
                    <h3 style="margin-top: 0; color: #3a0ca3;">🔗 Connect Further</h3>
                    <p style="margin: 10px 0;">
                        • <strong>Portfolio:</strong> <a href="{base_url}" style="color: #3a0ca3;">{base_url}</a><br>
                        • <strong>LinkedIn:</strong> <a href="https://linkedin.com/in/sri-ram-janjanam-0b4a86219" style="color: #3a0ca3;">SRI RAM JANJANAM</a><br>
                        • <strong>GitHub:</strong> <a href="https://github.com/SRIRAMJANJANAM" style="color: #3a0ca3;">SRIRAMJANJANAM</a><br>
                        • <strong>YouTube:</strong> <a href="https://youtube.com/@Pythonwebdeveloper_1" style="color: #3a0ca3;">Pythonwebdeveloper_1</a>
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <p style="margin: 0; font-style: italic; color: #3a0ca3;">
                        "I appreciate your interest and look forward to connecting with you soon!"
                    </p>
                    <p style="margin: 10px 0 0; font-weight: bold;">— Sri Ram Janjanam</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated confirmation email. Please do not reply to this email.</p>
                    <p>© {datetime.datetime.now().year} Sri Ram Portfolio</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    user_plain = f"""THANK YOU FOR CONTACTING SRI RAM JANJANAM

Hello {name},

Thank you for contacting Sri Ram Janjanam through his portfolio website!

✅ Your message has been received successfully.

📋 Your Submission:
• Name: {name}
• Email: {email}
{f'• Phone: {phone}' if phone else ''}
• Date: {datetime.datetime.now().strftime("%B %d, %Y")}

⏳ What happens next?
1. Sri Ram will review your message within 24-48 hours
2. You'll receive a personalized response at {email}
3. For urgent matters, connect via LinkedIn

🔗 Connect Further:
• Portfolio: {base_url}
• LinkedIn: https://linkedin.com/in/sri-ram-janjanam-0b4a86219
• GitHub: https://github.com/SRIRAMJANJANAM
• YouTube: https://youtube.com/@Pythonwebdeveloper_1

"I appreciate your interest and look forward to connecting with you soon!"
— Sri Ram Janjanam

This is an automated confirmation email.
"""
    
    try:
        # Send email to YOU (admin)
        send_mail(
            subject=admin_subject,
            message=strip_tags(admin_plain),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[YOUR_EMAIL],
            html_message=admin_html,
            fail_silently=True,
        )
        print(f"✅ Email sent to admin: {YOUR_EMAIL}")
        
        # Send confirmation email to USER
        send_mail(
            subject=user_subject,
            message=strip_tags(user_plain),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=user_html,
            fail_silently=True,
        )
        print(f"✅ Confirmation email sent to user: {email}")
        
        return True, None
        
    except Exception as e:
        error_msg = f"Email sending failed: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg


# Home view
def home_view(request):
    return render(request, 'testapp/base.html')


@never_cache
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        msg = request.POST.get('msg', '').strip()
        phone = request.POST.get('phone', '').strip() or None
        
        # Basic validation
        if not name or not email or not msg:
            return render(request, 'testapp/contact.html', {
                'error': 'Please fill in all required fields',
                'name': name,
                'email': email,
                'msg': msg,
                'phone': phone
            })
        
        # Save to database
        try:
            contact = Contact.objects.create(
                name=name, 
                email=email, 
                msg=msg,
                phone=phone
            )
            
            # Send emails using reusable function
            email_success, email_error = send_contact_emails(
                name=name,
                email=email,
                message=msg,
                phone=phone,
                source="Contact Form",
                request=request
            )
            
            if email_success:
                contact.email_sent = True
                contact.save(update_fields=['email_sent'])
            
            # Redirect to thank you page
            return redirect(f'/thanks/?name={name}&email={email}')
            
        except Exception as e:
            print(f"❌ Error saving contact: {e}")
            return render(request, 'testapp/contact.html', {
                'error': 'An error occurred. Please try again.',
                'name': name,
                'email': email,
                'msg': msg,
                'phone': phone
            })
    
    return render(request, 'testapp/contact.html')

# Skills view
def skill_view(request):
    return render(request, 'testapp/skills.html')

# Thank you page view
def thank_view(request):
    # Get parameters
    name = request.GET.get('name', '')
    email = request.GET.get('email', '')
    
    context = {
        'name': name if name else 'there',
        'email': email,
        'show_email_notice': bool(email)
    }
    
    return render(request, 'testapp/thanks.html', context)

# About page view
def about_view(request):
    return render(request, 'testapp/about.html')

# Experience list page view
def experience_view(request):
    experiences = Experience.objects.all().order_by('-start_date')
    return render(request, 'testapp/experience.html', {'experiences': experiences})

# ====================== CHATBOT FUNCTIONS ======================

def chatbot_response(user_message, request):
    """Enhanced chatbot logic with page links and contextual responses."""
    user_message = user_message.lower().strip()
    
    # Get base URL
    base_url = request.build_absolute_uri('/')[:-1]
    
    # Define page URLs
    pages = {
        'home': f"{base_url}/",
        'skills': f"{base_url}/skills/",
        'contact': f"{base_url}/contact/",
        'about': f"{base_url}/about/",
        'thanks': f"{base_url}/thanks/",
        'experiences': f"{base_url}/experiences/",
        'experience_api': f"{base_url}/api/experiences/"
    }

    # ===== NEW: Project/Business Discussion Detection =====
    project_discussion_keywords = [
        'i need to discuss', 'discuss about the project', 'project discussion',
        'business discussion', 'want to discuss', 'need to talk', 'like to discuss',
        'discuss project', 'discuss business', 'project talk', 'business talk',
        'collaborate on project', 'project collaboration', 'work on project',
        'new project', 'project idea', 'business proposal', 'proposal discussion',
        'discuss proposal', 'project meeting', 'business meeting'
    ]
    
    if any(phrase in user_message for phrase in project_discussion_keywords):
        return {
            "response": "project_discussion_trigger",
            "type": "project_discussion_flow"
        }

    # Greetings
    if any(word in user_message for word in ['hi', 'hello', 'hey', 'hola', 'greetings', 'hi there']):
        return {
            "response": "👋 Hello! Welcome to Sri Ram's portfolio. I can help you navigate through different sections. You can ask me about skills, projects, experience, contact information, or more!",
            "type": "text"
        }

    # Farewells
    elif any(word in user_message for word in ['bye', 'goodbye', 'see you', 'exit', 'quit']):
        return {
            "response": "👋 Goodbye! Thanks for visiting. Feel free to come back anytime if you have more questions!",
            "type": "text"
        }

    # Skills
    elif any(word in user_message for word in ['skill', 'what can you do', 'ability', 'technologies', 'technology', 'tech stack', 'programming']):
        return {
            "response": "Sri Ram has expertise in Full-Stack Development including: Python, Django, JavaScript, React, SQL,SqLite and modern web technologies.",
            "type": "link",
            "link_text": "View All Skills",
            "link_url": pages['skills']
        }

    # Contact - CHANGED: Return special trigger instead of link
    contact_keywords = ['contact', 'meet', 'reach', 'get in touch', 'email', 'phone', 'connect', 
                       'message', 'talk', 'communicate', 'reach out', 'collaborate', 'work together',
                       'i want to contact', 'need to contact', 'would like to contact', 'contact sri ram']
    
    if any(word in user_message for word in contact_keywords):
        return {
            "response": "contact_trigger",
            "type": "contact_flow"
        }

    # About
    elif any(word in user_message for word in ['about', 'who are you', 'introduction', 'background', 'who is sri ram']):
        return {
            "response": "Sri Ram Janjanam is a passionate Full-Stack Developer focused on building responsive, user-friendly applications with clean code and scalable architecture.",
            "type": "link",
            "link_text": "Know More About Me",
            "link_url": pages['about']
        }

    # Experience
    elif any(word in user_message for word in ['experience', 'work history', 'employment', 'job', 'career', 'professional', 'background', 'work']):
        return {
            "response": "Sri Ram has professional experience in web development with various technologies. He's worked on multiple projects and has a strong technical background.",
            "type": "link",
            "link_text": "View Experience Details",
            "link_url": pages['experiences']
        }

    # Projects
    elif any(word in user_message for word in ['project', 'portfolio', 'work', 'github', 'code', 'repository']):
        return {
            "response": "Sri Ram has worked on various projects including web applications, APIs, and full-stack solutions. Check out his GitHub for code samples!",
            "type": "html",
            "html_response": """
            You can find Sri Ram's projects on:<br><br>
            • <strong><a href="https://github.com/SRIRAMJANJANAM" target="_blank">GitHub</a></strong> - Code repositories<br>
            • <strong><a href="https://www.youtube.com/@Pythonwebdeveloper_1" target="_blank">YouTube</a></strong> - Tutorials and demos<br>
            • <strong>Portfolio</strong> - Various web applications
            """
        }

    # Home
    elif any(word in user_message for word in ['home', 'main', 'portfolio', 'start', 'beginning']):
        return {
            "response": "Here's the main portfolio page where you can learn more about Sri Ram and his work.",
            "type": "link",
            "link_text": "Go to Home",
            "link_url": pages['home']
        }

    # Thanks
    elif any(word in user_message for word in ['thanks', 'thank you', 'appreciate', 'thank']):
        return {
            "response": "You're welcome! Is there anything else I can help you with?",
            "type": "text"
        }

    # Help
    elif any(word in user_message for word in ['help', 'what can you do', 'options', 'commands', 'menu']):
        return {
            "response": "help",
            "type": "html",
            "html_response": """
            <div style="padding: 10px;">
                <h4 style="margin-bottom: 15px; color: var(--primary-color);">🤖 How I Can Help You:</h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #67d2c8;">
                        <strong>🎯 Skills</strong><br>
                        <small>Tech stack & abilities</small>
                    </div>
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #3a0ca3;">
                        <strong>💼 Experience</strong><br>
                        <small>Work history & background</small>
                    </div>
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #00ff0d;">
                        <strong>📞 Contact</strong><br>
                        <small>Get in touch</small>
                    </div>
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #f72585;">
                        <strong>👨‍💻 About</strong><br>
                        <small>Know about Sri Ram</small>
                    </div>
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #4cc9f0;">
                        <strong>📱 Phone</strong><br>
                        <small>Share your number</small>
                    </div>
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #ff6b6b;">
                        <strong>🚀 Projects</strong><br>
                        <small>See work samples</small>
                    </div>
                    <div style="background: rgba(103, 210, 200, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800;">
                        <strong>💼 Project Discussion</strong><br>
                        <small>Discuss business & projects</small>
                    </div>
                </div>
                <p style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    <strong>Tip:</strong> Just type what you're interested in, like "skills" or "contact me" or "I need to discuss a project"
                </p>
            </div>
            """
        }

    # Who made you
    elif any(word in user_message for word in ['name', 'who made you', 'developer', 'creator', 'who created you']):
        return {
            "response": "I'm the portfolio chatbot assistant created by Sri Ram Janjanam. I'm here to help you explore his portfolio and answer your questions!",
            "type": "text"
        }

    # Default response
    else:
        return {
            "response": "I'm here to help you explore Sri Ram's portfolio! You can ask me about:\n• Skills and technologies\n• Professional experience\n• Contact information\n• Projects and work\n• About Sri Ram\n• Project discussions and business proposals\n\nTry typing 'help' for more options!",
            "type": "text"
        }


@csrf_exempt
@ensure_csrf_cookie
def chat_view(request):
    """Main chatbot API endpoint"""
    if request.method == 'POST':
        try:
            # Parse JSON data
            try:
                data = json.loads(request.body.decode('utf-8'))
                user_message = data.get('message', '').strip()
            except:
                # Try form data as fallback
                user_message = request.POST.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({
                    'response': "Please enter a message.", 
                    'type': 'text'
                })

            # Initialize session
            if 'chat_state' not in request.session:
                request.session['chat_state'] = {}
            
            state = request.session['chat_state']
            user_message_lower = user_message.lower()
            
            # ===== CHECK IF USER IS CHANGING TOPIC =====
            # If user is in contact flow but sends a greeting or changes topic, clear the flow
            if 'contact_method_asked' in state and 'contact_method' not in state:
                break_topics = ['hi', 'hello', 'hey', 'bye', 'goodbye', 'help', 'skills', 
                              'projects', 'experience', 'about', 'home', 'thanks']
                
                if any(topic in user_message_lower for topic in break_topics):
                    request.session['chat_state'] = {}
                    state = request.session['chat_state']
                    request.session.modified = True
            
            # ===== NEW: PROJECT DISCUSSION FLOW HANDLING =====
            project_discussion_keywords = [
                'i need to discuss', 'discuss about the project', 'project discussion',
                'business discussion', 'want to discuss', 'need to talk', 'like to discuss',
                'discuss project', 'discuss business', 'project talk', 'business talk',
                'collaborate on project', 'project collaboration', 'work on project',
                'new project', 'project idea', 'business proposal', 'proposal discussion',
                'discuss proposal', 'project meeting', 'business meeting'
            ]
            
            is_project_discussion = any(phrase in user_message_lower for phrase in project_discussion_keywords)
            
            # Handle project discussion trigger
            if is_project_discussion and 'project_discussion_triggered' not in state:
                request.session['chat_state'] = {'project_discussion_triggered': True}
                state = request.session['chat_state']
                request.session.modified = True
                
                # Check if it's already set via chat contact
                if state.get('contact_method') == 'chat' and state.get('name'):
                    # If contact details already collected, use them for project discussion
                    name = state.get('name', '')
                    response_msg = f"Great {name}! You mentioned you'd like to discuss a project or business opportunity. "
                    response_msg += "Please share the details of what you'd like to discuss. Sri Ram will review your inquiry and get back to you shortly."
                    
                    return JsonResponse({
                        'response': response_msg,
                        'type': 'text'
                    })
                else:
                    # Ask how they want to contact first (similar to contact flow)
                    return JsonResponse({
                        'response': """
                        I'd be happy to help you discuss your project or business opportunity with Sri Ram! 💼<br><br>
                        
                        How would you prefer to proceed?<br><br>
                        
                        <div style="display: flex; flex-direction: column; gap: 12px; margin: 15px 0;">
                            <div style="padding: 14px; background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%); color: white; border-radius: 10px; text-align: left; cursor: pointer;" 
                                 onclick="document.getElementById('userInput').value='I want to use the contact page for project discussion'; document.getElementById('sendMessage').click();">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 18px;">📋</span>
                                    <div>
                                        <strong style="font-size: 16px;">Use Contact Page</strong><br>
                                        <small style="opacity: 0.9;">Structured form for project discussions</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="padding: 14px; background: white; color: #333; border: 2px solid #ff9800; border-radius: 10px; text-align: left; cursor: pointer;" 
                                 onclick="document.getElementById('userInput').value='Discuss via chat'; document.getElementById('sendMessage').click();">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 18px;">💬</span>
                                    <div>
                                        <strong style="font-size: 16px;">Discuss via Chat</strong><br>
                                        <small style="opacity: 0.9;">Share project details here in the chat</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <p style="margin-top: 15px; font-size: 14px; color: #666;">
                            <strong>💡 Note:</strong> For detailed project discussions, it's best to share your contact details first.
                        </p>
                        """,
                        'type': 'html'
                    })
            
            # Handle project discussion method selection
            if 'project_discussion_triggered' in state and 'project_discussion_method' not in state:
                page_selection_keywords = ['page', 'contact page', 'form', 'official', 'structured', 
                                          'use contact page', 'contact page', 'i want to use the contact page for project discussion']
                is_page_selected = any(word in user_message_lower for word in page_selection_keywords)
                
                chat_selection_keywords = ['chat', 'discuss', 'here', 'directly', 'via chat', 
                                          'discuss via chat', 'through chat', 'chat discussion']
                is_chat_selected = any(word in user_message_lower for word in chat_selection_keywords)
                
                if is_page_selected:
                    state['project_discussion_method'] = 'page'
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    base_url = request.build_absolute_uri('/')[:-1]
                    
                    return JsonResponse({
                        'response': f"""
                        Perfect! 📋<br><br>
                        
                        You'll be redirected to the contact page where you can:<br>
                        ✅ Provide project requirements<br>
                        ✅ Share timeline and budget<br>
                        ✅ Attach relevant files<br>
                        ✅ Get detailed response<br><br>
                        
                        <a href="{base_url}/contact/?project=discussion" target="_blank" 
                           style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%); 
                                  color: white; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 16px;
                                  box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);">
                            <i class="fas fa-external-link-alt"></i> Go to Contact Page for Project Discussion
                        </a>
                        
                        <br><br>
                        <p style="font-size: 14px; color: #666;">
                            <i class="fas fa-lightbulb"></i> Remember to mention it's for project discussion in your message!
                        </p>
                        """,
                        'type': 'html'
                    })
                
                elif is_chat_selected:
                    # If user chooses chat, check if they're already in contact flow
                    if state.get('contact_method') == 'chat' and state.get('name'):
                        # User already provided contact details, ask for project details
                        name = state.get('name', '')
                        return JsonResponse({
                            'response': f"""
                            Perfect! Let's discuss your project here. 💬<br><br>
                            
                            Hello {name}, please share:<br><br>
                            1. <strong>Project Overview</strong> (What you want to build)<br>
                            2. <strong>Timeline</strong> (When you need it)<br>
                            3. <strong>Budget Range</strong> (If any)<br>
                            4. <strong>Specific Requirements</strong><br><br>
                            
                            <strong>Please describe your project:</strong>
                            """,
                            'type': 'html'
                        })
                    else:
                        # User needs to provide contact details first
                        state['project_discussion_method'] = 'chat'
                        state['contact_method'] = 'chat'
                        request.session['chat_state'] = state
                        request.session.modified = True
                        
                        return JsonResponse({
                            'response': """
                            Great! Let's collect your contact information first, then discuss your project. 💬<br><br>
                            
                            I'll need a few details:<br>
                            1. <strong>Your Name</strong><br>
                            2. <strong>Email Address</strong><br>
                            3. <strong>Your Message about the project</strong><br><br>
                            
                            <em>Your information is secure and will only be used for project discussion.</em><br><br>
                            
                            <strong>To start, what's your name?</strong>
                            """,
                            'type': 'html'
                        })
                else:
                    return JsonResponse({
                        'response': """
                        I'm not sure which option you prefer for project discussion. Please choose:<br><br>
                        
                        Type <strong>"contact page"</strong> to use the official contact form<br>
                        OR<br>
                        Type <strong>"chat"</strong> to discuss here<br><br>
                        
                        How would you like to proceed with your project discussion?
                        """,
                        'type': 'html'
                    })
            
            # ===== ENHANCED CONTACT FLOW =====
            contact_keywords = ['contact', 'meet', 'reach', 'get in touch', 'email', 'phone', 'connect', 
                               'get in touch', 'email', 'whatsapp', 'telephone', 'mobile', 'cell',
                               'i want to contact', 'need to contact', 'would like to contact', 'contact sri ram']
            
            is_contact_request = any(word in user_message_lower for word in contact_keywords)
            
            if is_contact_request and 'contact_method_asked' not in state:
                request.session['chat_state'] = {'contact_method_asked': True}
                state = request.session['chat_state']
                request.session.modified = True
                
                return JsonResponse({
                    'response': """
                    I'd be happy to help you connect with Sri Ram! How would you like to proceed?<br><br>
                    
                    <div style="display: flex; flex-direction: column; gap: 12px; margin: 15px 0;">
                        <div style="padding: 14px; background: linear-gradient(135deg, #67d2c8 0%, #3a0ca3 100%); color: white; border-radius: 10px; text-align: left; cursor: pointer;" 
                             onclick="document.getElementById('userInput').value='I want to use the contact page'; document.getElementById('sendMessage').click();">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 18px;">📋</span>
                                <div>
                                    <strong style="font-size: 16px;">Use Contact Page</strong><br>
                                    <small style="opacity: 0.9;">Fill out the official contact form</small>
                                </div>
                            </div>
                        </div>
                        
                        <div style="padding: 14px; background: white; color: #333; border: 2px solid #67d2c8; border-radius: 10px; text-align: left; cursor: pointer;" 
                             onclick="document.getElementById('userInput').value='I prefer to chat'; document.getElementById('sendMessage').click();">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 18px;">💬</span>
                                <div>
                                    <strong style="font-size: 16px;">Contact via Chat</strong><br>
                                    <small style="opacity: 0.9;">Share your details here in the chat</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <p style="margin-top: 15px; font-size: 14px; color: #666;">
                        <strong>💡 Tip:</strong> The contact page has a structured form, while chat is more conversational.
                    </p>
                    """,
                    'type': 'html'
                })
            
            # Handle contact method selection
            if 'contact_method_asked' in state and 'contact_method' not in state:
                page_selection_keywords = ['page', 'contact page', 'form', 'official', 'structured', 'use contact page', 'contact page', 'i want to use the contact page']
                is_page_selected = any(word in user_message_lower for word in page_selection_keywords)
                
                chat_selection_keywords = ['chat', 'conversation', 'here', 'directly', 'prefer', 'via chat', 'i prefer to chat', 'through chat', 'chat contact']
                is_chat_selected = any(word in user_message_lower for word in chat_selection_keywords)
                
                if is_page_selected:
                    state['contact_method'] = 'page'
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    base_url = request.build_absolute_uri('/')[:-1]
                    
                    return JsonResponse({
                        'response': f"""
                        Excellent choice! 📋<br><br>
                        
                        You'll be redirected to the contact page where you can:<br>
                        ✅ Fill out a structured form<br>
                        ✅ Get confirmation email<br>
                        ✅ Track your inquiry<br><br>
                        
                        <a href="{base_url}/contact/" target="_blank" 
                           style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #67d2c8 0%, #3a0ca3 100%); 
                                  color: white; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 16px;
                                  box-shadow: 0 4px 15px rgba(103, 210, 200, 0.3);">
                            <i class="fas fa-external-link-alt"></i> Go to Contact Page
                        </a>
                        
                        <br><br>
                        <p style="font-size: 14px; color: #666;">
                            <i class="fas fa-clock"></i> You can also come back here if you change your mind!
                        </p>
                        """,
                        'type': 'html'
                    })
                
                elif is_chat_selected:
                    state['contact_method'] = 'chat'
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    return JsonResponse({
                        'response': """
                        Great! Let's collect your contact information here. 💬<br><br>
                        
                        I'll need a few details:<br>
                        1. <strong>Your Name</strong><br>
                        2. <strong>Email Address</strong><br>
                        3. <strong>Your Message</strong><br><br>
                        
                        <em>Don't worry, your information is secure and will only be used to contact you back.</em><br><br>
                        
                        <strong>To start, what's your name?</strong>
                        """,
                        'type': 'html'
                    })
                else:
                    return JsonResponse({
                        'response': """
                        I'm not sure which option you prefer. Please choose:<br><br>
                        
                        Type <strong>"contact page"</strong> to use the official contact form<br>
                        OR<br>
                        Type <strong>"chat"</strong> to share details here<br><br>
                        
                        Which would you prefer?
                        """,
                        'type': 'html'
                    })
            
            # ===== ENHANCED CHAT CONTACT FLOW =====
            if state.get('contact_method') == 'chat':
                # Check if user is trying to change topic during contact flow
                if user_message_lower in ['hi', 'hello', 'hey', 'bye', 'goodbye', 'help', 'cancel', 'stop']:
                    request.session['chat_state'] = {}
                    request.session.modified = True
                    bot_response = chatbot_response(user_message, request)
                    return JsonResponse({
                        'response': bot_response['response'],
                        'type': bot_response.get('type', 'text')
                    })
                
                # Step 1: Get name
                if 'name' not in state:
                    if len(user_message) < 2 or any(char.isdigit() for char in user_message):
                        return JsonResponse({
                            'response': "Please provide a valid name (at least 2 characters, no numbers). What's your name?",
                            'type': 'text'
                        })
                    
                    state['name'] = user_message.title()
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    # Check if this is for project discussion
                    if state.get('project_discussion_method') == 'chat':
                        return JsonResponse({
                            'response': f"""
                            Nice to meet you, {state['name']}! 👋<br><br>
                            
                            <strong>What's your email address?</strong><br>
                            <small>(We'll use this to discuss your project further)</small>
                            """,
                            'type': 'html'
                        })
                    else:
                        return JsonResponse({
                            'response': f"""
                            Nice to meet you, {state['name']}! 👋<br><br>
                            
                            <strong>What's your email address?</strong><br>
                            <small>(e.g., name@example.com)</small>
                            """,
                            'type': 'html'
                        })
                
                # Step 2: Get email
                elif 'name' in state and 'email' not in state:
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if re.match(email_pattern, user_message):
                        state['email'] = user_message
                        request.session['chat_state'] = state
                        request.session.modified = True
                        
                        # Check if this is for project discussion
                        if state.get('project_discussion_method') == 'chat':
                            return JsonResponse({
                                'response': f"""
                                Thanks {state['name']}! 📧<br><br>
                                
                                <strong>Now, please tell me about your project or business discussion:</strong><br>
                                <small>Describe what you'd like to discuss, timeline, requirements, etc.</small>
                                """,
                                'type': 'html'
                            })
                        else:
                            return JsonResponse({
                                'response': f"""
                                Thanks {state['name']}! 📧<br><br>
                                
                                <strong>Now, what's your phone number? (Optional)</strong><br>
                                <small>You can skip by typing "skip" or just press enter</small>
                                """,
                                'type': 'html'
                            })
                    else:
                        return JsonResponse({
                            'response': """
                            That doesn't look like a valid email address. 📧<br><br>
                            Please provide a valid email (e.g., name@example.com)<br><br>
                            <strong>What's your email address?</strong>
                            """,
                            'type': 'html'
                        })
                
                # Step 3: For project discussion via chat, skip phone and go directly to message
                elif (state.get('project_discussion_method') == 'chat' and 
                      'name' in state and 'email' in state and 'message' not in state):
                    
                    if len(user_message) < 10:
                        return JsonResponse({
                            'response': "Please provide more details about your project (at least 10 characters). What would you like to discuss?",
                            'type': 'text'
                        })
                    
                    state['message'] = user_message
                    state['phone'] = None  # Skip phone for project discussion
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    # Save to database and send emails
                    try:
                        base_url = request.build_absolute_uri('/')[:-1]
                        contact_msg = f"PROJECT DISCUSSION - Chatbot: {state['message']}"
                        
                        # Save to Contact model
                        contact = Contact.objects.create(
                            name=state['name'],
                            email=state['email'],
                            msg=contact_msg,
                            phone=state['phone']
                        )
                        
                        # ========== SEND EMAILS USING REUSABLE FUNCTION ==========
                        email_success, email_error = send_contact_emails(
                            name=state['name'],
                            email=state['email'],
                            message=contact_msg,
                            phone=state['phone'],
                            source="Project Discussion - Chatbot",
                            request=request
                        )
                        
                        if email_success:
                            contact.email_sent = True
                            contact.save(update_fields=['email_sent'])
                        
                        # Also save chat message
                        ChatMessage.objects.create(
                            user_name=state['name'],
                            user_email=state['email'],
                            user_phone=state['phone'],
                            message=state['message'],
                            response="Project discussion details saved successfully"
                        )
                        
                        # Prepare success summary
                        summary = f"""
                        <div style="background: black; padding: 20px; border-radius: 12px; border-left: 5px solid #ff9800;">
                            <h4 style="margin-top: 0; color: #ff9800;">✅ Project Discussion Details Saved!</h4>
                            
                            <div style="display: grid; grid-template-columns: 1fr; gap: 10px; margin: 15px 0;">
                                <div style="padding: 12px; background: rgba(255, 152, 0, 0.1); border-radius: 8px;">
                                    <strong style="color: #ff9800;">👤 Name:</strong> {state['name']}
                                </div>
                                <div style="padding: 12px; background: rgba(255, 152, 0, 0.1); border-radius: 8px;">
                                    <strong style="color: #ff9800;">📧 Email:</strong> {state['email']}
                                </div>
                                <div style="padding: 12px; background: rgba(255, 152, 0, 0.1); border-radius: 8px;">
                                    <strong style="color: #ff9800;">💼 Project Details:</strong> {state['message']}
                                </div>
                            </div>
                            
                            <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #28a745;">
                                <p style="margin: 0; color: #155724;">
                                    <i class="fas fa-check-circle" style="color: #28a745;"></i> 
                                    <strong>Success!</strong> Project discussion details sent to Sri Ram. He'll review and contact you at <strong>{state['email']}</strong>.
                                </p>
                            </div>
                            
                            <p style="margin-top: 15px; color: #666; font-size: 14px;">
                                <i class="fas fa-clock" style="color: #ffc107;"></i> 
                                Sri Ram will contact you within 24-48 hours to discuss your project in detail.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px; padding: 15px; border-radius: 8px;">
                            <strong>Thank you for sharing your project details! Is there anything else I can help you with?</strong>
                        </div>
                        """
                        
                        # Clear session state
                        request.session['chat_state'] = {}
                        request.session.modified = True
                        
                        return JsonResponse({
                            'response': summary,
                            'type': 'html'
                        })
                        
                    except Exception as e:
                        print(f"Error saving project discussion: {e}")
                        base_url = request.build_absolute_uri('/')[:-1]
                        
                        request.session['chat_state'] = {}
                        request.session.modified = True
                        
                        return JsonResponse({
                            'response': f"""
                            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545;">
                                <p style="margin: 0; color: #721c24;">
                                    <strong>⚠️ Error:</strong> Something went wrong. Please try using the 
                                    <a href="{base_url}/contact/?project=discussion" style="color: #dc3545; font-weight: bold;">Contact Page for Project Discussion</a> instead.
                                </p>
                            </div>
                            """,
                            'type': 'html'
                        })
                
                # Step 3: Get phone (optional) - for regular contact flow
                elif 'name' in state and 'email' in state and 'phone' not in state:
                    if user_message_lower in ['skip', 'no', 'none', 'not now', 'later', '']:
                        state['phone'] = None
                    else:
                        phone_clean = re.sub(r'\D', '', user_message)
                        
                        if phone_clean.startswith('91') and len(phone_clean) == 12:
                            phone_clean = phone_clean[2:]
                        elif phone_clean.startswith('91') and len(phone_clean) > 12:
                            phone_clean = phone_clean[2:12]
                        
                        indian_mobile_pattern = r'^[6789]\d{9}$'
                        
                        if re.match(indian_mobile_pattern, phone_clean):
                            formatted_phone = f"+91 {phone_clean[:5]} {phone_clean[5:]}"
                            state['phone'] = formatted_phone
                        else:
                            return JsonResponse({
                                'response': """
                                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                                    <p style="margin: 0; color: #856404;">
                                        <strong>📱 Invalid Indian Phone Number</strong><br><br>
                                        Please provide a valid Indian mobile number:<br>
                                        • Must be <strong>10 digits</strong><br>
                                        • Must start with <strong>6, 7, 8, or 9</strong><br>
                                        • Can include +91 country code<br><br>
                                        
                                        <strong>Examples:</strong><br>
                                        ✓ 9876543210<br>
                                        ✓ +91 98765 43210<br>
                                        ✓ 7890123456<br><br>
                                        
                                        Or type <strong>"skip"</strong> to skip this step<br><br>
                                        
                                        <strong>Phone number (optional):</strong>
                                    </p>
                                </div>
                                """,
                                'type': 'html'
                            })
                    
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    # If this is for project discussion, ask for project details
                    if state.get('project_discussion_triggered'):
                        return JsonResponse({
                            'response': f"""
                            Got it! 📱<br><br>
                            
                            <strong>Now, please tell me about your project or business discussion:</strong><br>
                            <small>Describe what you'd like to discuss, timeline, requirements, budget, etc.</small>
                            """,
                            'type': 'html'
                        })
                    else:
                        return JsonResponse({
                            'response': f"""
                            Got it! 📱<br><br>
                            
                            <strong>Finally, what's your message for Sri Ram?</strong><br>
                            <small>Tell us about your project, inquiry, or what you'd like to discuss</small>
                            """,
                            'type': 'html'
                        })
                
                # Step 4: Get message and send emails - for regular contact flow
                elif 'name' in state and 'email' in state and 'phone' in state and 'message' not in state:
                    if len(user_message) < 5:
                        return JsonResponse({
                            'response': "Please provide a message (at least 5 characters). What would you like to say?",
                            'type': 'text'
                        })
                    
                    state['message'] = user_message
                    request.session['chat_state'] = state
                    request.session.modified = True
                    
                    # Save to database and send emails
                    try:
                        base_url = request.build_absolute_uri('/')[:-1]
                        contact_msg = f"Chatbot contact: {state['message']}"
                        if state['phone']:
                            contact_msg += f"\nPhone: {state['phone']}"
                        
                        # Check if it's project discussion
                        if state.get('project_discussion_triggered'):
                            contact_msg = f"PROJECT DISCUSSION - {contact_msg}"
                            source = "Project Discussion - Chatbot"
                        else:
                            source = "Chatbot"
                        
                        # Save to Contact model
                        contact = Contact.objects.create(
                            name=state['name'],
                            email=state['email'],
                            msg=contact_msg,
                            phone=state['phone']
                        )
                        
                        # ========== SEND EMAILS USING REUSABLE FUNCTION ==========
                        email_success, email_error = send_contact_emails(
                            name=state['name'],
                            email=state['email'],
                            message=contact_msg,
                            phone=state['phone'],
                            source=source,
                            request=request
                        )
                        
                        if email_success:
                            contact.email_sent = True
                            contact.save(update_fields=['email_sent'])
                        
                        # Also save chat message
                        ChatMessage.objects.create(
                            user_name=state['name'],
                            user_email=state['email'],
                            user_phone=state['phone'],
                            message=state['message'],
                            response="Contact information saved and emails sent successfully"
                        )
                        
                        # Prepare success summary
                        phone_display = state['phone'] if state['phone'] else "Not provided"
                        
                        summary = f"""
                        <div style="background: black; padding: 20px; border-radius: 12px; border-left: 5px solid #67d2c8;">
                            <h4 style="margin-top: 0; color: #3a0ca3;">✅ Contact Information Saved Successfully!</h4>
                            
                            <div style="display: grid; grid-template-columns: 1fr; gap: 10px; margin: 15px 0;">
                                <div style=" padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <strong style="color: #67d2c8;">👤 Name:</strong> {state['name']}
                                </div>
                                <div style=" padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <strong style="color: #67d2c8;">📧 Email:</strong> {state['email']}
                                </div>
                                <div style=" padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <strong style="color: #67d2c8;">📱 Phone:</strong> {phone_display}
                                </div>
                                <div style=" padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <strong style="color: #67d2c8;">💬 Message:</strong> {state['message']}
                                </div>
                            </div>
                            
                            <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #28a745;">
                                <p style="margin: 0; color: #155724;">
                                    <i class="fas fa-check-circle" style="color: #28a745;"></i> 
                                    <strong>Success!</strong> Confirmation email sent to <strong>{state['email']}</strong>.
                                </p>
                            </div>
                            
                            <p style="margin-top: 15px; color: #666; font-size: 14px;">
                                <i class="fas fa-clock" style="color: #ffc107;"></i> 
                                Sri Ram will contact you soon. 
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px; padding: 15px;  border-radius: 8px;">
                            <strong>Thank you for reaching out! Is there anything else I can help you with?</strong>
                        </div>
                        """
                        
                        # Clear session state
                        request.session['chat_state'] = {}
                        request.session.modified = True
                        
                        return JsonResponse({
                            'response': summary,
                            'type': 'html'
                        })
                        
                    except Exception as e:
                        print(f"Error saving chatbot contact: {e}")
                        base_url = request.build_absolute_uri('/')[:-1]
                        
                        request.session['chat_state'] = {}
                        request.session.modified = True
                        
                        return JsonResponse({
                            'response': f"""
                            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545;">
                                <p style="margin: 0; color: #721c24;">
                                    <strong>⚠️ Error:</strong> Something went wrong. Please try using the 
                                    <a href="{base_url}/contact/" style="color: #dc3545; font-weight: bold;">Contact Page</a> instead.
                                </p>
                            </div>
                            """,
                            'type': 'html'
                        })
            
            # ===== REGULAR CHATBOT RESPONSE =====
            bot_response = chatbot_response(user_message, request)
            
            if bot_response.get('response') == 'project_discussion_trigger' and bot_response.get('type') == 'project_discussion_flow':
                request.session['chat_state'] = {'project_discussion_triggered': True}
                request.session.modified = True
                
                # Check if contact details already exist
                if state.get('contact_method') == 'chat' and state.get('name'):
                    name = state.get('name', '')
                    return JsonResponse({
                        'response': f"""
                        Great {name}! You mentioned you'd like to discuss a project or business opportunity. 💼<br><br>
                        
                        Please share the details of what you'd like to discuss. Include:<br><br>
                        1. <strong>Project Overview</strong><br>
                        2. <strong>Timeline</strong><br>
                        3. <strong>Budget Range</strong> (if any)<br>
                        4. <strong>Specific Requirements</strong><br><br>
                        
                        <strong>Describe your project:</strong>
                        """,
                        'type': 'html'
                    })
                else:
                    return JsonResponse({
                        'response': """
                        I'd be happy to help you discuss your project or business opportunity with Sri Ram! 💼<br><br>
                        
                        How would you prefer to proceed?<br><br>
                        
                        <div style="display: flex; flex-direction: column; gap: 12px; margin: 15px 0;">
                            <div style="padding: 14px; background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%); color: white; border-radius: 10px; text-align: left; cursor: pointer;" 
                                 onclick="document.getElementById('userInput').value='I want to use the contact page for project discussion'; document.getElementById('sendMessage').click();">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 18px;">📋</span>
                                    <div>
                                        <strong style="font-size: 16px;">Use Contact Page</strong><br>
                                        <small style="opacity: 0.9;">Structured form for project discussions</small>
                                    </div>
                                </div>
                            </div>
                            
                            <div style="padding: 14px; background: white; color: #333; border: 2px solid #ff9800; border-radius: 10px; text-align: left; cursor: pointer;" 
                                 onclick="document.getElementById('userInput').value='Discuss via chat'; document.getElementById('sendMessage').click();">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 18px;">💬</span>
                                    <div>
                                        <strong style="font-size: 16px;">Discuss via Chat</strong><br>
                                        <small style="opacity: 0.9;">Share project details here in the chat</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <p style="margin-top: 15px; font-size: 14px; color: #666;">
                            <strong>💡 Note:</strong> For detailed project discussions, it's best to share your contact details first.
                        </p>
                        """,
                        'type': 'html'
                    })
            
            elif bot_response.get('response') == 'contact_trigger' and bot_response.get('type') == 'contact_flow':
                request.session['chat_state'] = {'contact_method_asked': True}
                request.session.modified = True
                
                return JsonResponse({
                    'response': """
                    I'd be happy to help you connect with Sri Ram! How would you like to proceed?<br><br>
                    
                    <div style="display: flex; flex-direction: column; gap: 12px; margin: 15px 0;">
                        <div style="padding: 14px; background: linear-gradient(135deg, #67d2c8 0%, #3a0ca3 100%); color: white; border-radius: 10px; text-align: left; cursor: pointer;" 
                             onclick="document.getElementById('userInput').value='I want to use the contact page'; document.getElementById('sendMessage').click();">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 18px;">📋</span>
                                <div>
                                    <strong style="font-size: 16px;">Use Contact Page</strong><br>
                                    <small style="opacity: 0.9;">Fill out the official contact form</small>
                                </div>
                            </div>
                        </div>
                        
                        <div style="padding: 14px; background: white; color: #333; border: 2px solid #67d2c8; border-radius: 10px; text-align: left; cursor: pointer;" 
                             onclick="document.getElementById('userInput').value='I prefer to chat'; document.getElementById('sendMessage').click();">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 18px;">💬</span>
                                <div>
                                    <strong style="font-size: 16px;">Contact via Chat</strong><br>
                                    <small style="opacity: 0.9;">Share your details here in the chat</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <p style="margin-top: 15px; font-size: 14px; color: #666;">
                        <strong>💡 Tip:</strong> The contact page has a structured form, while chat is more conversational.
                    </p>
                    """,
                    'type': 'html'
                })
            
            if bot_response.get('type') == 'link':
                response_data = {
                    'response': bot_response['response'],
                    'type': 'link',
                    'link_text': bot_response['link_text'],
                    'link_url': bot_response['link_url']
                }
            elif bot_response.get('type') == 'html' or bot_response.get('html_response'):
                response_data = {
                    'response': bot_response.get('html_response', bot_response['response']),
                    'type': 'html'
                }
            else:
                response_data = {
                    'response': bot_response['response'],
                    'type': 'text'
                }
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON format in request',
                'type': 'error'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Server error: {str(e)}',
                'type': 'error'
            }, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'status': 'online',
            'message': 'Chatbot API is running',
            'endpoints': {
                'chat': '/chat/ (POST)',
                'help': 'Send POST request with {"message": "your text"}'
            }
        })
    
    else:
        return JsonResponse({
            'error': 'Method not allowed',
            'type': 'error'
        }, status=405)

@csrf_exempt
def chat_clear_session(request):
    """Clear chatbot session data"""
    if 'chat_state' in request.session:
        del request.session['chat_state']
        request.session.modified = True
    
    return JsonResponse({
        'status': 'success',
        'message': 'Chat session cleared'
    })

@csrf_exempt
def chat_status(request):
    """Check chatbot status"""
    state = request.session.get('chat_state', {})
    
    status_info = {
        'status': 'online',
        'session_active': len(state) > 0,
        'session_data': state,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    return JsonResponse(status_info)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def experience_list_api(request):
    """API endpoint to list all experiences or create a new one"""
    
    if request.method == 'GET':
        # Get all experiences
        experiences = Experience.objects.all().order_by('-start_date')
        
        # Format experiences as a list of dictionaries
        data = []
        for exp in experiences:
            experience_data = {
                'id': exp.id,
                'role': exp.role,
                'company': exp.company,
                'start_date': exp.start_date.strftime('%Y-%m-%d'),
                'currently_working': exp.currently_working,
                'description': exp.description
            }
            
            # Handle end date based on currently_working flag
            if exp.currently_working:
                experience_data['end_date'] = 'Present'
            elif exp.end_date:
                experience_data['end_date'] = exp.end_date.strftime('%Y-%m-%d')
            else:
                experience_data['end_date'] = None
                
            data.append(experience_data)
        
        return JsonResponse({'experiences': data}, safe=False)
    
    elif request.method == 'POST':
        # Create new experience
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['role', 'company', 'start_date']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse(
                        {'error': f'{field} is required'}, 
                        status=400
                    )
            
            # Parse dates
            try:
                start_date = datetime.datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                
                # Handle end date
                end_date = None
                if 'end_date' in data and data['end_date']:
                    if data['end_date'].lower() != 'present':
                        end_date = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=400
                )
            
            # Validate currently_working logic
            currently_working = data.get('currently_working', False)
            if currently_working and end_date:
                return JsonResponse(
                    {'error': 'Cannot have end_date when currently_working is true'},
                    status=400
                )
            
            # Validate date logic
            if end_date and start_date > end_date:
                return JsonResponse(
                    {'error': 'start_date cannot be after end_date'},
                    status=400
                )
            
            # Create experience
            experience = Experience.objects.create(
                role=data['role'],
                company=data['company'],
                start_date=start_date,
                end_date=end_date,
                currently_working=currently_working,
                description=data.get('description', '')
            )
            
            response_data = {
                'message': 'Experience created successfully',
                'id': experience.id,
                'role': experience.role,
                'company': experience.company,
                'start_date': experience.start_date.strftime('%Y-%m-d'),
                'currently_working': experience.currently_working,
                'description': experience.description
            }
            
            if experience.currently_working:
                response_data['end_date'] = 'Present'
            elif experience.end_date:
                response_data['end_date'] = experience.end_date.strftime('%Y-%m-%d')
            else:
                response_data['end_date'] = None
                
            return JsonResponse(response_data, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def experience_detail_api(request, experience_id):
    """API endpoint to get, update or delete a specific experience"""
    try:
        experience = Experience.objects.get(id=experience_id)
    except Experience.DoesNotExist:
        return JsonResponse({'error': 'Experience not found'}, status=404)
    
    if request.method == 'GET':
        # Return specific experience
        data = {
            'id': experience.id,
            'role': experience.role,
            'company': experience.company,
            'start_date': experience.start_date.strftime('%Y-%m-%d'),
            'currently_working': experience.currently_working,
            'description': experience.description
        }
        
        if experience.currently_working:
            data['end_date'] = 'Present'
        elif experience.end_date:
            data['end_date'] = experience.end_date.strftime('%Y-%m-%d')
        else:
            data['end_date'] = None
            
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        # Update experience
        try:
            data = json.loads(request.body)
            
            # Update fields if provided
            if 'role' in data:
                experience.role = data['role']
            if 'company' in data:
                experience.company = data['company']
            if 'description' in data:
                experience.description = data['description']
            
            # Handle dates
            if 'start_date' in data:
                try:
                    experience.start_date = datetime.datetime.strptime(
                        data['start_date'], '%Y-%m-%d'
                    ).date()
                except ValueError:
                    return JsonResponse(
                        {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                        status=400
                    )
            
            # Handle currently_working and end_date logic
            if 'currently_working' in data:
                currently_working = data['currently_working']
                experience.currently_working = currently_working
                
                if currently_working:
                    experience.end_date = None
                elif 'end_date' in data and data['end_date']:
                    if data['end_date'].lower() == 'present':
                        experience.currently_working = True
                        experience.end_date = None
                    else:
                        try:
                            experience.end_date = datetime.datetime.strptime(
                                data['end_date'], '%Y-%m-%d'
                            ).date()
                        except ValueError:
                            return JsonResponse(
                                {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                                status=400
                            )
            elif 'end_date' in data:
                # Only end_date is provided
                if data['end_date']:
                    if data['end_date'].lower() == 'present':
                        experience.currently_working = True
                        experience.end_date = None
                    else:
                        try:
                            experience.end_date = datetime.datetime.strptime(
                                data['end_date'], '%Y-%m-%d'
                            ).date()
                            experience.currently_working = False
                        except ValueError:
                            return JsonResponse(
                                {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                                status=400
                            )
                else:
                    # Empty end_date means currently working
                    experience.end_date = None
                    experience.currently_working = True
            
            # Validate date logic
            if experience.end_date and experience.start_date > experience.end_date:
                return JsonResponse(
                    {'error': 'start_date cannot be after end_date'},
                    status=400
                )
            
            experience.save()
            
            response_data = {
                'message': 'Experience updated successfully',
                'id': experience.id,
                'role': experience.role,
                'company': experience.company,
                'start_date': experience.start_date.strftime('%Y-%m-%d'),
                'currently_working': experience.currently_working,
                'description': experience.description
            }
            
            if experience.currently_working:
                response_data['end_date'] = 'Present'
            elif experience.end_date:
                response_data['end_date'] = experience.end_date.strftime('%Y-%m-%d')
            else:
                response_data['end_date'] = None
                
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'DELETE':
        # Delete experience
        experience.delete()
        return JsonResponse({'message': 'Experience deleted successfully'})

# ====================== BULK OPERATIONS ======================

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def experience_bulk_api(request):
    """API endpoint for bulk operations"""
    
    if request.method == 'POST':
        # Bulk create experiences
        try:
            data = json.loads(request.body)
            
            if not isinstance(data, list):
                return JsonResponse({'error': 'Expected a list of experiences'}, status=400)
            
            created_experiences = []
            errors = []
            
            for idx, exp_data in enumerate(data):
                try:
                    # Validate required fields
                    required_fields = ['role', 'company', 'start_date']
                    for field in required_fields:
                        if field not in exp_data or not exp_data[field]:
                            errors.append(f"Item {idx}: {field} is required")
                            continue
                    
                    # Parse dates
                    start_date = datetime.datetime.strptime(exp_data['start_date'], '%Y-%m-%d').date()
                    
                    end_date = None
                    if 'end_date' in exp_data and exp_data['end_date']:
                        if exp_data['end_date'].lower() != 'present':
                            end_date = datetime.datetime.strptime(exp_data['end_date'], '%Y-%m-%d').date()
                    
                    # Validate currently_working logic
                    currently_working = exp_data.get('currently_working', False)
                    if currently_working and end_date:
                        errors.append(f"Item {idx}: Cannot have end_date when currently_working is true")
                        continue
                    
                    # Validate date logic
                    if end_date and start_date > end_date:
                        errors.append(f"Item {idx}: start_date cannot be after end_date")
                        continue
                    
                    # Create experience
                    experience = Experience.objects.create(
                        role=exp_data['role'],
                        company=exp_data['company'],
                        start_date=start_date,
                        end_date=end_date,
                        currently_working=currently_working,
                        description=exp_data.get('description', '')
                    )
                    
                    created_experiences.append({
                        'id': experience.id,
                        'role': experience.role,
                        'company': experience.company
                    })
                    
                except ValueError as e:
                    errors.append(f"Item {idx}: Invalid date format - {str(e)}")
                except Exception as e:
                    errors.append(f"Item {idx}: {str(e)}")
            
            response_data = {
                'created_count': len(created_experiences),
                'created_experiences': created_experiences
            }
            
            if errors:
                response_data['errors'] = errors
                response_data['error_count'] = len(errors)
                return JsonResponse(response_data, status=207)  # Multi-status
            
            return JsonResponse(response_data, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    elif request.method == 'DELETE':
        # Bulk delete experiences
        try:
            data = json.loads(request.body)
            
            if 'ids' not in data or not isinstance(data['ids'], list):
                return JsonResponse({'error': 'Expected a list of IDs in "ids" field'}, status=400)
            
            deleted_count, _ = Experience.objects.filter(id__in=data['ids']).delete()
            
            return JsonResponse({
                'message': f'Successfully deleted {deleted_count} experiences',
                'deleted_count': deleted_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

# ====================== SEARCH AND FILTER API ======================

@require_http_methods(["GET"])
def experience_search_api(request):
    """API endpoint to search and filter experiences"""
    
    # Get query parameters
    company = request.GET.get('company', '')
    role = request.GET.get('role', '')
    start_year = request.GET.get('start_year', '')
    end_year = request.GET.get('end_year', '')
    currently_working = request.GET.get('currently_working', '')
    
    # Start with all experiences
    experiences = Experience.objects.all()
    
    # Apply filters
    if company:
        experiences = experiences.filter(company__icontains=company)
    
    if role:
        experiences = experiences.filter(role__icontains=role)
    
    if start_year:
        try:
            start_year = int(start_year)
            experiences = experiences.filter(start_date__year=start_year)
        except ValueError:
            pass
    
    if end_year:
        try:
            end_year = int(end_year)
            experiences = experiences.filter(end_date__year=end_year)
        except ValueError:
            pass
    
    if currently_working.lower() == 'true':
        experiences = experiences.filter(currently_working=True)
    elif currently_working.lower() == 'false':
        experiences = experiences.filter(currently_working=False)
    
    # Order by start date (most recent first)
    experiences = experiences.order_by('-start_date')
    
    # Format response
    data = []
    for exp in experiences:
        experience_data = {
            'id': exp.id,
            'role': exp.role,
            'company': exp.company,
            'start_date': exp.start_date.strftime('%Y-%m-%d'),
            'currently_working': exp.currently_working,
            'description': exp.description
        }
        
        if exp.currently_working:
            experience_data['end_date'] = 'Present'
        elif exp.end_date:
            experience_data['end_date'] = exp.end_date.strftime('%Y-%m-%d')
        else:
            experience_data['end_date'] = None
            
        data.append(experience_data)
    
    return JsonResponse({
        'count': len(data),
        'experiences': data,
        'filters_applied': {
            'company': company,
            'role': role,
            'start_year': start_year,
            'end_year': end_year,
            'currently_working': currently_working
        }
    })

# ====================== STATISTICS API ======================

@require_http_methods(["GET"])
def experience_stats_api(request):
    """API endpoint to get experience statistics"""
    
    total_experiences = Experience.objects.count()
    current_jobs = Experience.objects.filter(currently_working=True).count()
    past_jobs = Experience.objects.filter(currently_working=False).count()
    
    # Get unique companies
    unique_companies = Experience.objects.values('company').distinct().count()
    
    # Get earliest and latest dates
    earliest_start = Experience.objects.earliest('start_date').start_date
    latest_start = Experience.objects.latest('start_date').start_date
    
    # Calculate total experience duration (in months)
    total_months = 0
    for exp in Experience.objects.all():
        if exp.currently_working:
            end_date = datetime.date.today()
        elif exp.end_date:
            end_date = exp.end_date
        else:
            continue
        
        # Calculate months difference
        months = (end_date.year - exp.start_date.year) * 12 + (end_date.month - exp.start_date.month)
        total_months += max(0, months)
    
    total_years = total_months / 12 if total_months > 0 else 0
    
    return JsonResponse({
        'total_experiences': total_experiences,
        'current_jobs': current_jobs,
        'past_jobs': past_jobs,
        'unique_companies': unique_companies,
        'earliest_start_date': earliest_start.strftime('%Y-%m-%d'),
        'latest_start_date': latest_start.strftime('%Y-%m-%d'),
        'total_experience_months': total_months,
        'total_experience_years': round(total_years, 1)
    })

# ====================== EXPORT API ======================

@require_http_methods(["GET"])
def experience_export_api(request):
    """API endpoint to export experiences in different formats"""
    
    format_type = request.GET.get('format', 'json').lower()
    experiences = Experience.objects.all().order_by('-start_date')
    
    if format_type == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="experiences.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Role', 'Company', 'Start Date', 'End Date', 'Currently Working', 'Description'])
        
        for exp in experiences:
            end_date = 'Present' if exp.currently_working else (exp.end_date.strftime('%Y-%m-%d') if exp.end_date else 'N/A')
            writer.writerow([
                exp.role,
                exp.company,
                exp.start_date.strftime('%Y-%m-%d'),
                end_date,
                'Yes' if exp.currently_working else 'No',
                exp.description
            ])
        
        return response
    
    elif format_type == 'pdf':
        # Note: For PDF, you'll need to install reportlab or use a template
        # This is a simplified version - you might want to use a proper PDF library
        from django.http import HttpResponse
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="experiences.pdf"'
        
        # Simple text-based PDF content
        pdf_content = "Experience List\n\n"
        for exp in experiences:
            end_date = 'Present' if exp.currently_working else (exp.end_date.strftime('%Y-%m-%d') if exp.end_date else 'N/A')
            pdf_content += f"Role: {exp.role}\n"
            pdf_content += f"Company: {exp.company}\n"
            pdf_content += f"Start Date: {exp.start_date.strftime('%Y-%m-%d')}\n"
            pdf_content += f"End Date: {end_date}\n"
            pdf_content += f"Description: {exp.description}\n"
            pdf_content += "-" * 50 + "\n"
        
        response.write(pdf_content)
        return response
    
    else:  # Default to JSON
        data = []
        for exp in experiences:
            experience_data = {
                'role': exp.role,
                'company': exp.company,
                'start_date': exp.start_date.strftime('%Y-%m-%d'),
                'currently_working': exp.currently_working,
                'description': exp.description
            }
            
            if exp.currently_working:
                experience_data['end_date'] = 'Present'
            elif exp.end_date:
                experience_data['end_date'] = exp.end_date.strftime('%Y-%m-%d')
            else:
                experience_data['end_date'] = None
                
            data.append(experience_data)
        
        return JsonResponse({'experiences': data})