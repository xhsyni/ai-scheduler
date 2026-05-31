import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import { makeStore } from "./redux/store";

export const getRouter = () => {
  const queryClient = new QueryClient();
  const store = makeStore();

  const router = createRouter({
    routeTree,
    context: { queryClient, store },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  });

  return router;
};
