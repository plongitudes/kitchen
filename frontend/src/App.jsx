import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Recipes from './pages/Recipes';
import RecipeNew from './pages/RecipeNew';
import RecipeEdit from './pages/RecipeEdit';
import RecipeDetail from './pages/RecipeDetail';
import ScheduleList from './pages/ScheduleList';
import ScheduleNew from './pages/ScheduleNew';
import ScheduleDetail from './pages/ScheduleDetail';
import TemplateList from './pages/TemplateList';
import TemplateNew from './pages/TemplateNew';
import TemplateEdit from './pages/TemplateEdit';
import TemplateDetail from './pages/TemplateDetail';
import MealPlanCurrent from './pages/MealPlanCurrent';
import MealPlanList from './pages/MealPlanList';
import MealPlanDetail from './pages/MealPlanDetail';
import GroceryListAll from './pages/GroceryListAll';
import GroceryListDetail from './pages/GroceryListDetail';
import Ingredients from './pages/Ingredients';
import Settings from './pages/Settings';
import System7Demo from './pages/System7Demo';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/system7-demo" element={<System7Demo />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Home />} />
              <Route path="recipes" element={<Recipes />} />
              <Route path="recipes/new" element={<RecipeNew />} />
              <Route path="recipes/:id" element={<RecipeDetail />} />
              <Route path="recipes/:id/edit" element={<RecipeEdit />} />
              <Route path="schedules" element={<ScheduleList />} />
              <Route path="schedules/new" element={<ScheduleNew />} />
              <Route path="schedules/:id" element={<ScheduleDetail />} />
              <Route path="templates" element={<TemplateList />} />
              <Route path="templates/new" element={<TemplateNew />} />
              <Route path="templates/:id/edit" element={<TemplateEdit />} />
              <Route path="templates/:id" element={<TemplateDetail />} />
              <Route path="meal-plans/current" element={<MealPlanCurrent />} />
              <Route path="meal-plans/:id" element={<MealPlanDetail />} />
              <Route path="meal-plans" element={<MealPlanList />} />
              <Route path="grocery-lists/:id" element={<GroceryListDetail />} />
              <Route path="grocery-lists" element={<GroceryListAll />} />
              <Route path="ingredients" element={<Ingredients />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
