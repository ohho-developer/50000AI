from django import forms
from django.contrib.auth.models import User
from .models import Profile


class ProfileForm(forms.ModelForm):
    """사용자 프로필 폼"""
    
    class Meta:
        model = Profile
        fields = [
            'gender', 'birth_date', 'height', 'weight'
        ]
        widgets = {
            'gender': forms.Select(attrs={
                'class': 'w-full bg-gray-dark/50 border border-gray-600 rounded-xl px-4 py-3 text-white focus:border-accent focus:ring-2 focus:ring-accent/20 focus:outline-none transition-all duration-200'
            }),
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full bg-gray-dark/50 border border-gray-600 rounded-xl px-4 py-3 text-white focus:border-accent focus:ring-2 focus:ring-accent/20 focus:outline-none transition-all duration-200'
            }),
            'height': forms.NumberInput(attrs={
                'step': '0.1',
                'min': '100',
                'max': '250',
                'class': 'w-full bg-gray-dark/50 border border-gray-600 rounded-xl px-4 py-3 text-white focus:border-accent focus:ring-2 focus:ring-accent/20 focus:outline-none transition-all duration-200'
            }),
            'weight': forms.NumberInput(attrs={
                'step': '0.1',
                'min': '30',
                'max': '300',
                'class': 'w-full bg-gray-dark/50 border border-gray-600 rounded-xl px-4 py-3 text-white focus:border-accent focus:ring-2 focus:ring-accent/20 focus:outline-none transition-all duration-200'
            }),
        }
        labels = {
            'gender': '성별',
            'birth_date': '생년월일',
            'height': '키 (cm)',
            'weight': '체중 (kg)',
        }
        help_texts = {
            'height': '정확한 키를 입력해주세요 (100-250cm)',
            'weight': '현재 체중을 입력해주세요 (30-300kg)',
        }


class FoodAnalysisForm(forms.Form):
    """음식 분석 입력 폼"""
    
    food_text = forms.CharField(
        label='오늘 무엇을 드셨나요?',
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-gray-dark/50 border border-gray-600 rounded-xl px-4 py-4 text-white placeholder-gray-400 focus:border-accent focus:ring-2 focus:ring-accent/20 focus:outline-none transition-all duration-200 resize-none',
            'placeholder': '예: 아침은 굶었고 점심에 제육덮밥, 저녁엔 삼겹살 2인분에 소주 한 병 마셨어요',
            'rows': 4,
        }),
        help_text='자연어로 편하게 입력해주세요. AI가 분석하여 영양 정보를 제공합니다.',
        max_length=1000
    )
