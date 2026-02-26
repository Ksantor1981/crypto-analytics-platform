import { apiClient } from './index';

export const channelsApi = {
  getChannels: apiClient.getChannels,
  getChannel: apiClient.getChannel,
  createChannel: apiClient.createChannel,
  updateChannel: apiClient.updateChannel,
  deleteChannel: apiClient.deleteChannel,
};
