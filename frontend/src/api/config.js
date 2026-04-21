import service from './index'

/**
 * LLM 설정 API
 */

// 현재 LLM 설정 조회
export const getLLMConfig = () => {
  return service.get('/api/config/llm')
}

// LLM 설정 변경
export const updateLLMConfig = (config) => {
  return service.put('/api/config/llm', config)
}

// 프리셋 목록 조회
export const getLLMPresets = () => {
  return service.get('/api/config/llm/presets')
}
