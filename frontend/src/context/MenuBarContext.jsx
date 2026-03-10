import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';

const MenuBarContext = createContext(null);

// eslint-disable-next-line react-refresh/only-export-components
export const useMenuBar = () => {
  const context = useContext(MenuBarContext);
  if (!context) {
    throw new Error('useMenuBar must be used within a MenuBarProvider');
  }
  return context;
};

// eslint-disable-next-line react-refresh/only-export-components
export const usePageActions = (actions, deps = []) => {
  const context = useContext(MenuBarContext);
  if (!context) {
    throw new Error('usePageActions must be used within a MenuBarProvider');
  }
  const { setPageActions } = context;

  useEffect(() => {
    setPageActions(actions);
    return () => setPageActions([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
};

// eslint-disable-next-line react-refresh/only-export-components
export const useSectionActions = (sectionId, actions, deps = []) => {
  const context = useContext(MenuBarContext);
  if (!context) {
    throw new Error('useSectionActions must be used within a MenuBarProvider');
  }
  const { registerSection, unregisterSection } = context;

  useEffect(() => {
    registerSection(sectionId, actions);
    return () => unregisterSection(sectionId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionId, ...deps]);
};

export const MenuBarProvider = ({ children }) => {
  const [pageActions, setPageActions] = useState([]);
  const [sectionActions, setSectionActions] = useState([]);
  const sectionsRef = useRef(new Map());

  const rebuildSectionActions = useCallback(() => {
    const allActions = [];
    for (const [, section] of sectionsRef.current.entries()) {
      allActions.push(...section.actions);
    }
    setSectionActions(allActions);
  }, []);

  const registerSection = useCallback((id, actions) => {
    sectionsRef.current.set(id, { actions });
    rebuildSectionActions();
  }, [rebuildSectionActions]);

  const unregisterSection = useCallback((id) => {
    sectionsRef.current.delete(id);
    rebuildSectionActions();
  }, [rebuildSectionActions]);

  return (
    <MenuBarContext.Provider
      value={{
        pageActions,
        sectionActions,
        setPageActions,
        registerSection,
        unregisterSection,
      }}
    >
      {children}
    </MenuBarContext.Provider>
  );
};
