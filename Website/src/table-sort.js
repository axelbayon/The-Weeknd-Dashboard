/**
 * table-sort.js
 * 
 * Système de tri cliquable pour les tables Songs et Albums.
 * 
 * Fonctionnalités :
 * - Tri ascendant/descendant sur toutes les colonnes utiles
 * - Indicateurs visuels : flèches ▲/▼, état actif (couleur accent)
 * - Accessibilité : ARIA aria-sort, role="columnheader"
 * - Tri alphabétique ignorant les * initiaux (featuring)
 * - Collator français pour les accents
 */

(function() {
  'use strict';

  /**
   * Collator français pour tri avec accents
   */
  const frCollator = new Intl.Collator('fr', { 
    sensitivity: 'base',
    numeric: true 
  });

  /**
   * État du tri actuel
   */
  let currentSort = {
    column: 'streams_total', // Colonne par défaut
    direction: 'desc',        // desc par défaut
    table: null               // Référence à la table
  };

  /**
   * Configuration des colonnes triables
   * key: data attribute, sortType: 'number' | 'text' | 'title'
   */
  const sortableColumns = {
    songs: [
      { key: 'rank', sortType: 'number', label: '#' },
      { key: 'title', sortType: 'title', label: 'Titre' },
      { key: 'streams_total', sortType: 'number', label: 'Streams totaux' },
      { key: 'streams_daily', sortType: 'number', label: 'Streams quotidiens' },
      { key: 'variation', sortType: 'number', label: 'Variation (%)' },
      { key: 'days_to_next_cap', sortType: 'number', label: 'Prochain cap (j)' },
      { key: 'next_cap', sortType: 'text', label: 'Prochain palier' }
    ],
    albums: [
      { key: 'rank', sortType: 'number', label: '#' },
      { key: 'title', sortType: 'title', label: 'Titre' },
      { key: 'streams_total', sortType: 'number', label: 'Streams totaux' },
      { key: 'streams_daily', sortType: 'number', label: 'Streams quotidiens' },
      { key: 'variation', sortType: 'number', label: 'Variation (%)' },
      { key: 'days_to_next_cap', sortType: 'number', label: 'Prochain cap (j)' },
      { key: 'next_cap', sortType: 'text', label: 'Prochain palier' }
    ]
  };

  /**
   * Normalise un titre pour le tri (ignore * et ^ initiaux, minuscules, sans accents)
   * Garde * et ^ dans l'affichage mais les ignore pour le tri (Prompt 7.9)
   */
  function normalizeTitle(title) {
    if (!title) return '';
    // Retire * ou ^ au début pour le tri (featuring / compilation)
    const cleaned = title.replace(/^[\*\^]\s*/, '').trim();
    console.log(`[DEBUG] normalizeTitle: "${title}" -> "${cleaned}"`);
    return cleaned;
  }

  /**
   * Compare deux valeurs selon le type
   */
  function compareValues(a, b, sortType) {
    // Gérer les valeurs nulles/undefined
    if (a === null || a === undefined) return 1;
    if (b === null || b === undefined) return -1;

    switch (sortType) {
      case 'number':
        // Convertir en nombre, gérer N.D. ou texte
        const numA = parseFloat(String(a).replace(/[^\d.-]/g, '')) || 0;
        const numB = parseFloat(String(b).replace(/[^\d.-]/g, '')) || 0;
        return numA - numB;

      case 'title':
        // Tri alphabétique avec Collator FR, ignore *
        const titleA = normalizeTitle(String(a));
        const titleB = normalizeTitle(String(b));
        return frCollator.compare(titleA, titleB);

      case 'text':
      default:
        // Tri texte standard avec Collator FR
        return frCollator.compare(String(a), String(b));
    }
  }

  /**
   * Trie les lignes du tbody selon la colonne et la direction
   */
  function sortTable(table, columnKey, sortType, direction) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr[data-row-id]'));

    rows.sort((rowA, rowB) => {
      const cellA = rowA.querySelector(`[data-sort-value="${columnKey}"]`);
      const cellB = rowB.querySelector(`[data-sort-value="${columnKey}"]`);

      if (!cellA || !cellB) return 0;

      const valueA = cellA.getAttribute('data-sort-raw') || cellA.textContent.trim();
      const valueB = cellB.getAttribute('data-sort-raw') || cellB.textContent.trim();

      const comparison = compareValues(valueA, valueB, sortType);
      return direction === 'asc' ? comparison : -comparison;
    });

    // Réinsérer les lignes triées
    rows.forEach(row => tbody.appendChild(row));

    // Ne PAS mettre à jour les rangs visuels - ils doivent rester figés au rang Kworb d'origine
  }

  /**
   * Met à jour l'état visuel des headers (flèches, ARIA, classe active)
   */
  function updateHeaderStates(thead, activeColumn, direction) {
    const headers = thead.querySelectorAll('th[data-sort-key]');

    headers.forEach(th => {
      const sortKey = th.getAttribute('data-sort-key');
      const button = th.querySelector('.data-table__sort-button');
      const iconContainer = th.querySelector('.data-table__sort-icon');

      if (sortKey === activeColumn) {
        // Actif
        th.classList.add('is-sorted');
        th.setAttribute('aria-sort', direction === 'asc' ? 'ascending' : 'descending');
        
        if (button) {
          button.classList.add('data-table__sort-button--active');
        }

        // Afficher flèche
        if (iconContainer) {
          iconContainer.textContent = direction === 'asc' ? '▲' : '▼';
          iconContainer.setAttribute('aria-hidden', 'false');
        }
      } else {
        // Inactif
        th.classList.remove('is-sorted');
        th.setAttribute('aria-sort', 'none');
        
        if (button) {
          button.classList.remove('data-table__sort-button--active');
        }

        // Masquer flèche
        if (iconContainer) {
          iconContainer.textContent = '';
          iconContainer.setAttribute('aria-hidden', 'true');
        }
      }
    });
  }

  /**
   * Gère le clic sur un header pour trier
   * Écoute au niveau du thead, résout avec closest('th[data-sort-key]') (Prompt 7.8)
   */
  function handleHeaderClick(event) {
    // Résoudre le <th> cliqué via closest (plein-surface)
    const th = event.target.closest('th[data-sort-key]');
    if (!th) return;

    const table = th.closest('table');
    const thead = th.closest('thead');
    const columnKey = th.getAttribute('data-sort-key');
    const sortType = th.getAttribute('data-sort-type');

    // Toggle direction si même colonne, sinon descendre
    let newDirection = 'desc';
    if (currentSort.column === columnKey && currentSort.table === table) {
      newDirection = currentSort.direction === 'asc' ? 'desc' : 'asc';
    }

    // Sauvegarder état
    currentSort = {
      column: columnKey,
      direction: newDirection,
      table: table
    };

    // Trier
    sortTable(table, columnKey, sortType, newDirection);

    // Mettre à jour visuels
    updateHeaderStates(thead, columnKey, newDirection);

    console.log(`[TableSort] Tri appliqué : ${columnKey} ${newDirection}`);
  }

  /**
   * Initialise le tri pour une table
   */
  function initTableSort(tableSelector, tableType) {
    const table = document.querySelector(tableSelector);
    if (!table) {
      console.warn(`[TableSort] Table non trouvée : ${tableSelector}`);
      return;
    }

    const thead = table.querySelector('thead');
    if (!thead) return;

    const columns = sortableColumns[tableType];
    if (!columns) {
      console.warn(`[TableSort] Type de table inconnu : ${tableType}`);
      return;
    }

    // Ajouter data-sort-key et data-sort-type à chaque <th>
    columns.forEach(col => {
      const th = Array.from(thead.querySelectorAll('th')).find(header => {
        const text = header.textContent.trim().toLowerCase();
        return text.includes(col.label.toLowerCase());
      });

      if (th) {
        th.setAttribute('data-sort-key', col.key);
        th.setAttribute('data-sort-type', col.sortType);
        th.setAttribute('role', 'columnheader');
        th.setAttribute('aria-sort', 'none');

        // Ajouter container pour icône de tri (si button existe)
        const button = th.querySelector('.data-table__sort-button');
        if (button && !th.querySelector('.data-table__sort-icon')) {
          const icon = document.createElement('span');
          icon.className = 'data-table__sort-icon';
          icon.setAttribute('aria-hidden', 'true');
          button.appendChild(icon);
        }
      }
    });

    // Attacher événement clic
    thead.addEventListener('click', handleHeaderClick);

    // Appliquer tri par défaut (streams_total desc)
    const defaultColumn = 'streams_total';
    const defaultSortType = 'number';
    currentSort = {
      column: defaultColumn,
      direction: 'desc',
      table: table
    };

    sortTable(table, defaultColumn, defaultSortType, 'desc');
    updateHeaderStates(thead, defaultColumn, 'desc');

    console.log(`[TableSort] Initialisé pour ${tableType} avec tri par défaut : ${defaultColumn} desc`);
  }

  /**
   * API publique
   */
  window.tableSort = {
    /**
     * Initialise le tri pour les tables Songs et Albums
     */
    init() {
      console.log('[TableSort] Initialisation du système de tri');
      // Attendre que les tables soient rendues par data-renderer
      // On initialise après un court délai
      setTimeout(() => {
        initTableSort('.data-table--songs', 'songs');
        initTableSort('.data-table--albums', 'albums');
      }, 100);
    },

    /**
     * Réinitialise le tri après un rendu de table
     */
    reinitTable(tableType) {
      const selector = `.data-table--${tableType}`;
      initTableSort(selector, tableType);
    },

    /**
     * Obtient l'état du tri actuel
     */
    getCurrentSort() {
      return { ...currentSort };
    }
  };

  console.log('[TableSort] Module chargé');
})();
