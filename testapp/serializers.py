from rest_framework import serializers
from testapp.models import Experience

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'role', 'company', 'start_date', 'end_date', 'currently_working', 'description']







# {
#     "role": "Python Develpoer",
#     "company": "ORAI Robotics",
#     "start_date": "2025-07-07",
#     "currently_working": false,
#     "description": "Developing web applications using Django,Restapi,React and Mysql"
# }