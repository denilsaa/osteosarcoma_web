import { Link } from "react-router-dom";

import "./MockupPage.css";

type MockupPageProps = {
  title: string;
  description: string;
  actionLabel?: string;
  actionTo?: string;
};

export function MockupPage({
  title,
  description,
  actionLabel,
  actionTo,
}: MockupPageProps) {
  return (
    <div className="mockup-page">
      <div className="mockup-page__header">
        <div>
          <span className="mockup-page__eyebrow">
            Sistema de apoyo clínico
          </span>

          <h1>{title}</h1>

          <p>{description}</p>
        </div>

        {actionLabel && actionTo && (
          <Link
            className="mockup-page__action"
            to={actionTo}
          >
            {actionLabel}
          </Link>
        )}
      </div>

      <div className="mockup-page__card">
        <div className="mockup-page__placeholder">
          <strong>{title}</strong>

          <span>
            Mockup navegable en construcción
          </span>
        </div>
      </div>
    </div>
  );
}