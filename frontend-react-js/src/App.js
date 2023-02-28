import "./App.css";

import React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import ConfirmationPage from "./pages/ConfirmationPage";
import HomeFeedPage from "./pages/HomeFeedPage";
import MessageGroupPage from "./pages/MessageGroupPage";
import MessageGroupsPage from "./pages/MessageGroupsPage";
import NotificationPage from "./pages/NotificationPage";
import RecoverPage from "./pages/RecoverPage";
import SigninPage from "./pages/SigninPage";
import SignupPage from "./pages/SignupPage";
import UserFeedPage from "./pages/UserFeedPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <HomeFeedPage />,
  },
  {
    path: "/@:handle",
    element: <UserFeedPage />,
  },
  {
    path: "/notifications",
    element: <NotificationPage />,
  },
  {
    path: "/messages",
    element: <MessageGroupsPage />,
  },
  {
    path: "/messages/@:handle",
    element: <MessageGroupPage />,
  },
  {
    path: "/signup",
    element: <SignupPage />,
  },
  {
    path: "/signin",
    element: <SigninPage />,
  },
  {
    path: "/confirm",
    element: <ConfirmationPage />,
  },
  {
    path: "/forgot",
    element: <RecoverPage />,
  },
]);

function App() {
  return (
    <>
      <RouterProvider router={router} />
    </>
  );
}

export default App;
