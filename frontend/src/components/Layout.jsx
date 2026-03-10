import { Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MenuBarProvider } from '../context/MenuBarContext';
import MenuBar from './MenuBar';

const Layout = () => {
  const { user } = useAuth();

  if (!user) {
    return <Outlet />;
  }

  return (
    <MenuBarProvider>
      <div className="h-screen flex flex-col overflow-hidden">
        <MenuBar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </MenuBarProvider>
  );
};

export default Layout;
