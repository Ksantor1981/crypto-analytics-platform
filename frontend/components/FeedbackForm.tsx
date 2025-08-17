import React, { useState } from 'react';
import { Button, TextField, Select, MenuItem, FormControl, InputLabel, Alert, Box, Typography, Paper } from '@mui/material';

interface FeedbackFormData {
  feedback_type: 'question' | 'suggestion' | 'bug_report' | 'feature_request' | 'general';
  subject: string;
  message: string;
  user_email: string;
  user_telegram: string;
}

const FeedbackForm: React.FC = () => {
  const [formData, setFormData] = useState<FeedbackFormData>({
    feedback_type: 'general',
    subject: '',
    message: '',
    user_email: '',
    user_telegram: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'success' | 'error' | null>(null);
  const [submitMessage, setSubmitMessage] = useState('');

  const handleInputChange = (field: keyof FeedbackFormData) => (
    event: React.ChangeEvent<HTMLInputElement | { value: unknown }>
  ) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    });
  };

  const validateForm = (): boolean => {
    if (!formData.subject.trim()) {
      setSubmitMessage('Пожалуйста, укажите тему сообщения');
      setSubmitStatus('error');
      return false;
    }

    if (!formData.message.trim() || formData.message.length < 10) {
      setSubmitMessage('Сообщение должно содержать минимум 10 символов');
      setSubmitStatus('error');
      return false;
    }

    if (formData.user_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.user_email)) {
      setSubmitMessage('Пожалуйста, укажите корректный email адрес');
      setSubmitStatus('error');
      return false;
    }

    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          user_email: formData.user_email || undefined,
          user_telegram: formData.user_telegram || undefined,
        }),
      });

      if (response.ok) {
        setSubmitStatus('success');
        setSubmitMessage('Спасибо за вашу обратную связь! Мы ответим вам в ближайшее время.');
        
        // Очищаем форму
        setFormData({
          feedback_type: 'general',
          subject: '',
          message: '',
          user_email: '',
          user_telegram: ''
        });
      } else {
        const errorData = await response.json();
        setSubmitStatus('error');
        setSubmitMessage(errorData.detail || 'Произошла ошибка при отправке обратной связи');
      }
    } catch (error) {
      setSubmitStatus('error');
      setSubmitMessage('Произошла ошибка при отправке обратной связи. Пожалуйста, попробуйте позже.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const feedbackTypes = [
    { value: 'question', label: '❓ Вопрос', description: 'Задать вопрос о продукте' },
    { value: 'suggestion', label: '💡 Предложение', description: 'Предложить улучшения' },
    { value: 'bug_report', label: '🐛 Ошибка', description: 'Сообщить о проблеме' },
    { value: 'feature_request', label: '🚀 Функция', description: 'Запросить новую функцию' },
    { value: 'general', label: '📝 Общее', description: 'Любое другое сообщение' }
  ];

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Typography variant="h4" component="h2" gutterBottom align="center">
        📝 Обратная связь
      </Typography>
      
      <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3 }}>
        Есть вопросы или предложения? Мы будем рады услышать от вас!
      </Typography>

      {submitStatus && (
        <Alert severity={submitStatus} sx={{ mb: 3 }}>
          {submitMessage}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Тип обратной связи</InputLabel>
          <Select
            value={formData.feedback_type}
            label="Тип обратной связи"
            onChange={handleInputChange('feedback_type')}
          >
            {feedbackTypes.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                <Box>
                  <Typography variant="body1">{type.label}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {type.description}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="Тема сообщения"
          value={formData.subject}
          onChange={handleInputChange('subject')}
          required
          sx={{ mb: 3 }}
          placeholder="Например: Проблема с отображением сигналов"
        />

        <TextField
          fullWidth
          label="Ваше сообщение"
          value={formData.message}
          onChange={handleInputChange('message')}
          required
          multiline
          rows={6}
          sx={{ mb: 3 }}
          placeholder="Опишите подробно ваш вопрос, предложение или проблему. Чем больше деталей, тем лучше мы сможем вам помочь!"
        />

        <TextField
          fullWidth
          label="Email (необязательно)"
          type="email"
          value={formData.user_email}
          onChange={handleInputChange('user_email')}
          sx={{ mb: 3 }}
          placeholder="your@email.com"
          helperText="Для получения ответа на ваш email"
        />

        <TextField
          fullWidth
          label="Telegram username (необязательно)"
          value={formData.user_telegram}
          onChange={handleInputChange('user_telegram')}
          sx={{ mb: 3 }}
          placeholder="@username"
          helperText="Для связи через Telegram"
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={isSubmitting}
          sx={{ mt: 2 }}
        >
          {isSubmitting ? 'Отправка...' : 'Отправить обратную связь'}
        </Button>
      </Box>

      <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          💡 <strong>Советы:</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          • Чем подробнее вы опишете проблему, тем быстрее мы сможем помочь
        </Typography>
        <Typography variant="body2" color="text.secondary">
          • Если сообщаете об ошибке, укажите шаги для её воспроизведения
        </Typography>
        <Typography variant="body2" color="text.secondary">
          • Мы отвечаем на все сообщения в течение 24 часов
        </Typography>
      </Box>
    </Paper>
  );
};

export default FeedbackForm;
