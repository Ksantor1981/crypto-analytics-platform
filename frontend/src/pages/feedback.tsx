import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
} from '@mui/material';
import Head from 'next/head';

import FeedbackForm from '@/components/FeedbackForm';

const FeedbackPage: React.FC = () => {
  return (
    <>
      <Head>
        <title>Обратная связь - Crypto Analytics Platform</title>
        <meta
          name="description"
          content="Свяжитесь с нами для вопросов, предложений или сообщения об ошибках"
        />
      </Head>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box textAlign="center" mb={4}>
          <Typography variant="h3" component="h1" gutterBottom>
            📝 Обратная связь
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            Есть вопросы или предложения? Мы будем рады услышать от вас!
          </Typography>
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            gap: 4,
          }}
        >
          {/* Форма обратной связи */}
          <Box sx={{ flex: { xs: 1, md: 2 } }}>
            <FeedbackForm />
          </Box>

          {/* Информационная панель */}
          <Box sx={{ flex: { xs: 1, md: 1 } }}>
            <Box sx={{ position: 'sticky', top: 20 }}>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    💬 Способы связи
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Выберите наиболее удобный для вас способ связи:
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="primary">
                      📧 Email
                    </Typography>
                    <Typography variant="body2">
                      support@cryptoanalytics.com
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="primary">
                      📱 Telegram
                    </Typography>
                    <Typography variant="body2">@CryptoAnalyticsBot</Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      🌐 Веб-форма
                    </Typography>
                    <Typography variant="body2">
                      Заполните форму слева
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    ⏱️ Время ответа
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Мы стремимся отвечать на все сообщения как можно быстрее:
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="success.main">
                      🚀 Срочные вопросы
                    </Typography>
                    <Typography variant="body2">В течение 2-4 часов</Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="warning.main">
                      📝 Обычные вопросы
                    </Typography>
                    <Typography variant="body2">В течение 24 часов</Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="info.main">
                      💡 Предложения
                    </Typography>
                    <Typography variant="body2">В течение 48 часов</Typography>
                  </Box>
                </CardContent>
              </Card>

              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>💡 Совет:</strong> Чем подробнее вы опишете проблему
                  или вопрос, тем быстрее мы сможем вам помочь!
                </Typography>
              </Alert>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    📋 Часто задаваемые вопросы
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Возможно, ответ на ваш вопрос уже есть здесь:
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="primary">
                      ❓ Как работает система сигналов?
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Система анализирует данные из множества источников...
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="primary">
                      💰 Платформа бесплатная?
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Базовый функционал бесплатный, премиум функции...
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="primary">
                      🔒 Безопасны ли мои данные?
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Мы используем современные методы шифрования...
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </Box>

        {/* Дополнительная информация */}
        <Box sx={{ mt: 6, p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
          <Typography variant="h5" gutterBottom align="center">
            🎯 Наша миссия
          </Typography>
          <Typography variant="body1" align="center" paragraph>
            Мы стремимся создать лучшую платформу для анализа криптовалютных
            сигналов. Ваша обратная связь помогает нам улучшать продукт и делать
            его более полезным для всех пользователей.
          </Typography>

          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 2,
              mt: 2,
            }}
          >
            <Box sx={{ flex: 1 }} textAlign="center">
              <Typography variant="h4" color="primary">
                🚀
              </Typography>
              <Typography variant="h6">Быстро</Typography>
              <Typography variant="body2" color="text.secondary">
                Быстрые ответы на все вопросы
              </Typography>
            </Box>

            <Box sx={{ flex: 1 }} textAlign="center">
              <Typography variant="h4" color="primary">
                💎
              </Typography>
              <Typography variant="h6">Качественно</Typography>
              <Typography variant="body2" color="text.secondary">
                Профессиональная поддержка
              </Typography>
            </Box>

            <Box sx={{ flex: 1 }} textAlign="center">
              <Typography variant="h4" color="primary">
                🤝
              </Typography>
              <Typography variant="h6">Дружелюбно</Typography>
              <Typography variant="body2" color="text.secondary">
                Приветливое общение
              </Typography>
            </Box>
          </Box>
        </Box>
      </Container>
    </>
  );
};

export default FeedbackPage;
