// Cypress support file for E2E tests
// https://docs.cypress.io/guides/tooling/plugins-guide.html

// Custom command to login
Cypress.Commands.add(
  'login',
  (_username: string, _password: string) => {
    cy.visit('/login');
    cy.get('input[name="username"]').type(_username);
    cy.get('input[name="password"]').type(_password);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  }
);

export {};
