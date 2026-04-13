// 系统配置相关接口
import apiService from './api'

export interface AssetTypeOption {
  value: string
  label: string
}

export interface SystemOptionsAPI {
  asset_types: AssetTypeOption[]
  departments: string[]
}

// 获取系统选项（设备类型和部门）
export const getSystemOptions = async (): Promise<SystemOptionsAPI> => {
  const response = await apiService.get<SystemOptionsAPI>('/system-config/options')
  return response
}

// 获取设备类型列表
export const getAssetTypes = async (): Promise<AssetTypeOption[]> => {
  const response = await apiService.get<AssetTypeOption[]>('/system-config/asset-types')
  return response
}

// 更新设备类型列表
export const updateAssetTypes = async (assetTypes: AssetTypeOption[]): Promise<AssetTypeOption[]> => {
  const response = await apiService.put<AssetTypeOption[]>('/system-config/asset-types', assetTypes)
  return response
}

// 获取部门列表
export const getDepartments = async (): Promise<string[]> => {
  const response = await apiService.get<string[]>('/system-config/departments')
  return response
}

// 更新部门列表
export const updateDepartments = async (departments: string[]): Promise<string[]> => {
  const response = await apiService.put<string[]>('/system-config/departments', departments)
  return response
}
