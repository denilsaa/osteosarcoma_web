import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  useAuth,
} from "./AuthProvider";


export function ProtectedRoute() {

  const location =
    useLocation();


  const {
    autenticado,
  } = useAuth();


  if (!autenticado) {

    return (

      <Navigate

        to="/login"

        replace

        state={{

          from:
            location.pathname,

        }}

      />

    );

  }


  return <Outlet />;

}