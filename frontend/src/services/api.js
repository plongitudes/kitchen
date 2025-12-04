// eslint-disable-next-line no-restricted-imports -- This is the centralized API instance
import axios from 'axios';

// Create axios instance without baseURL initially
const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token and set baseURL from runtime config
api.interceptors.request.use(
  (config) => {
    // Get API URL from runtime config (injected at container startup) or fall back to localhost
    // This is evaluated at request time, ensuring window.APP_CONFIG is available
    
    // Debug logging
    console.log('🔍 DEBUG - window.APP_CONFIG:', window.APP_CONFIG);
    console.log('🔍 DEBUG - window.APP_CONFIG?.API_URL:', window.APP_CONFIG?.API_URL);
    console.log('🔍 DEBUG - Type:', typeof window.APP_CONFIG?.API_URL);
    
    const apiUrl = window.APP_CONFIG?.API_URL || 'http://localhost:8000';
    console.log('🔍 DEBUG - Final apiUrl:', apiUrl);
    console.log('🔍 DEBUG - Setting config.baseURL to:', apiUrl);
    
    config.baseURL = apiUrl;
    
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  register: (username, password) =>
    api.post('/auth/register', { username, password }),

  login: (username, password) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  getCurrentUser: () => api.get('/me'),
  listUsers: () => api.get('/auth/users'),
};

// Recipe API
export const recipeAPI = {
  list: (params) => api.get('/recipes', { params }),
  get: (id) => api.get(`/recipes/${id}`),
  create: (data) => api.post('/recipes', data),
  update: (id, data) => api.put(`/recipes/${id}`, data),
  delete: (id) => api.delete(`/recipes/${id}`),
  restore: (id) => api.post(`/recipes/${id}/restore`),
  importPreview: (url) => api.post('/recipes/import-preview', { url }),
  reimport: (id) => api.post(`/recipes/${id}/reimport`),
  
  // Prep steps
  getPrepSteps: (id) => api.get(`/recipes/${id}/prep-steps`),
  createPrepStep: (id, data) => api.post(`/recipes/${id}/prep-steps`, data),
  
  // Ingredients
  updateIngredient: (recipeId, ingredientId, data) => 
    api.patch(`/recipes/${recipeId}/ingredients/${ingredientId}`, data),
};

// Template API
export const templateAPI = {
  list: (params) => api.get('/templates', { params }),
  get: (id) => api.get(`/templates/${id}`),
  create: (data) => api.post('/templates', data),
  update: (id, data) => api.put(`/templates/${id}`, data),
  fork: (id, newName) => api.post(`/templates/${id}/fork`, { new_name: newName }),
  retire: (id) => api.delete(`/templates/${id}`),
  hardDelete: (id) => api.delete(`/templates/${id}/hard`),
};

// Schedule API
export const scheduleAPI = {
  list: () => api.get('/schedules'),
  get: (id) => api.get(`/schedules/${id}`),
  create: (data) => api.post('/schedules', data),
  update: (id, data) => api.put(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),

  // Template management
  getCurrentTemplate: (sequenceId) => api.get(`/schedules/${sequenceId}/current-template`),
  addTemplate: (sequenceId, data) => api.post(`/schedules/${sequenceId}/templates`, data),
  removeTemplate: (sequenceId, templateId) => api.delete(`/schedules/${sequenceId}/templates/${templateId}`),
  reorderTemplates: (sequenceId, templateIds) => api.put(`/schedules/${sequenceId}/templates/reorder`, { template_ids: templateIds }),
};

// Meal Plan API
export const mealPlanAPI = {
  list: (limit) => api.get('/meal-plans', { params: { limit } }),
  get: (id) => api.get(`/meal-plans/${id}`),
  getCurrent: (sequenceId) => api.get('/meal-plans/current', { params: { sequence_id: sequenceId } }),
  advanceWeek: (sequenceId) => api.post('/meal-plans/advance-week', { sequence_id: sequenceId }),
  startOnWeek: (sequenceId, data) => api.post('/meal-plans/start-on-week', data, { params: { sequence_id: sequenceId } }),

  // Grocery lists
  generateGroceryList: (instanceId, shoppingDate) =>
    api.post(`/meal-plans/${instanceId}/grocery-lists/generate`, { shopping_date: shoppingDate }),
  listGroceryLists: (instanceId) => api.get(`/meal-plans/${instanceId}/grocery-lists`),
  getGroceryList: (id) => api.get(`/meal-plans/grocery-lists/${id}`),
  listAllGroceryLists: () => api.get('/meal-plans/grocery-lists/all'),

  // Meal assignments (per-instance modifications)
  listAssignments: (instanceId) => api.get(`/meal-plans/${instanceId}/assignments`),
  createAssignment: (instanceId, data) => api.post(`/meal-plans/${instanceId}/assignments`, data),
  updateAssignment: (instanceId, assignmentId, data) => api.put(`/meal-plans/${instanceId}/assignments/${assignmentId}`, data),
  deleteAssignment: (instanceId, assignmentId) => api.delete(`/meal-plans/${instanceId}/assignments/${assignmentId}`),
};

// Ingredient API
export const ingredientAPI = {
  listIngredients: (search, category) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    return api.get(`/ingredients?${params.toString()}`);
  },
  getIngredient: (id) => api.get(`/ingredients/${id}`),
  createIngredient: (data) => api.post('/ingredients', data),
  updateIngredient: (id, data) => api.put(`/ingredients/${id}`, data),
  deleteIngredient: (id) => api.delete(`/ingredients/${id}`),
  deleteAlias: (ingredientId, aliasId) => api.delete(`/ingredients/${ingredientId}/aliases/${aliasId}`),
  listUnmapped: () => api.get('/ingredients/unmapped'),
  getRecipesForUnmapped: (ingredientName) =>
    api.get(`/ingredients/unmapped/${encodeURIComponent(ingredientName)}/recipes`),
  mapIngredient: (ingredientName, commonIngredientId) =>
    api.post('/ingredients/map', { ingredient_name: ingredientName, common_ingredient_id: commonIngredientId }),
  createWithMapping: (name, category, initialAlias) =>
    api.post('/ingredients/create-with-mapping', { name, category, initial_alias: initialAlias }),
  mergeIngredients: (sourceIds, targetId) =>
    api.post('/ingredients/merge', { source_ingredient_ids: sourceIds, target_ingredient_id: targetId }),
  autoMapCommon: (minRecipeCount = 2) =>
    api.post(`/ingredients/auto-map?min_recipe_count=${minRecipeCount}`),
};
