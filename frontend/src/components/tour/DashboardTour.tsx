import React from 'react';
import Joyride, { Step, CallBackProps } from 'react-joyride';

interface DashboardTourProps {
  run: boolean;
  setRun: (run: boolean) => void;
}

const DashboardTour: React.FC<DashboardTourProps> = ({ run, setRun }) => {
  const steps: Step[] = [
    {
      target: '.dashboard-header',
      content: 'Добро пожаловать на вашу панель управления! Здесь собрана вся ключевая информация.',
      placement: 'bottom',
    },
    {
      target: '.key-metrics',
      content: 'Это ваши ключевые метрики. Следите за своей производительностью здесь.',
      placement: 'bottom',
    },
    {
      target: '.add-channel-button',
      content: 'Нажмите здесь, чтобы добавить свой первый Telegram-канал для анализа.',
      placement: 'right',
    },
    {
      target: '.followed-channels-list',
      content: 'Здесь будут отображаться каналы, которые вы отслеживаете.',
      placement: 'top',
    },
    {
      target: '.recent-activity-feed',
      content: 'Лента последних действий покажет вам актуальные события и сигналы.',
      placement: 'top',
    },
  ];

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status } = data;
    const finishedStatuses: string[] = ['finished', 'skipped'];

    if (finishedStatuses.includes(status)) {
      setRun(false);
      // Можно добавить логику, чтобы тур не показывался снова, например, сохранить в localStorage
      localStorage.setItem('dashboardTourCompleted', 'true');
    }
  };

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showProgress
      showSkipButton
      callback={handleJoyrideCallback}
      locale={{
        back: 'Назад',
        close: 'Закрыть',
        last: 'Завершить',
        next: 'Далее',
        skip: 'Пропустить',
      }}
      styles={{
        options: {
          arrowColor: '#fff',
          backgroundColor: '#fff',
          primaryColor: '#007bff',
          textColor: '#333',
          zIndex: 1000,
        },
      }}
    />
  );
};

export default DashboardTour;
