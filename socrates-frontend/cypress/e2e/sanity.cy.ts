// Basic sanity E2E tests
describe('Frontend Sanity Tests', () => {
  it('should load the application', () => {
    cy.visit('/');
  });

  it('should have a login page', () => {
    cy.visit('/login');
    cy.contains('Login').should('exist');
  });
});
