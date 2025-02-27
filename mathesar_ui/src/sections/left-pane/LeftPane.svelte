<script lang="ts">
  import { get } from 'svelte/store';
  import { faTable } from '@fortawesome/free-solid-svg-icons';
  import {
    Icon,
    Tree,
  } from '@mathesar-components';
  import {
    addTab,
  } from '@mathesar/stores/tabs';
  import {
    tables,
  } from '@mathesar/stores/tables';
  import {
    loadIncompleteImport,
  } from '@mathesar/stores/fileImports';

  import type {
    DBTablesStoreData,
  } from '@mathesar/stores/tables';
  import type { MathesarTab } from '@mathesar/stores/tabs';
  import type { SchemaEntry, TableEntry } from '@mathesar/App.d';
  import type {
    TreeItem,
  } from '@mathesar-components/types';

  export let database: string;
  export let schemaId: SchemaEntry['id'];
  export let activeTab;
  export let getLink: (entry: MathesarTab) => string;
  
  let tree: TreeItem[] = [];
  let activeTable: Set<unknown>;
  const expandedItems = new Set(['table_header']);

  function generateTree(_tables: DBTablesStoreData) {
    const tableHeader = {
      treeId: 'table_header',
      id: 't_h',
      label: 'Tables',
      tables: [] as MathesarTab[],
    };

    _tables?.data?.forEach((value) => {
      const tableInfo: MathesarTab = {
        ...value,
        label: value.name,
        treeId: value.id,
      };
      if (value.import_verified === false) {
        tableInfo.label += '*';
        tableInfo.treeId = `_existing_${value.id}`;
      }
      tableHeader.tables.push(tableInfo);
    });
    return [tableHeader];
  }

  $: tree = generateTree($tables);

  function onActiveTabChange(_activeTab: MathesarTab) {
    activeTable = new Set([_activeTab?.id]);
  }

  $: onActiveTabChange(activeTab);

  function tableSelected(e: { detail: { node: TableEntry, originalEvent: Event, link?: string } }) {
    const { node, originalEvent } = e.detail;
    originalEvent.preventDefault();

    let newTab: MathesarTab = {
      id: node.id,
      label: node.name,
    };
    if (node.import_verified === false) {
      const fileImport = loadIncompleteImport(database, schemaId, node);
      newTab = {
        ...newTab,
        id: get(fileImport).id,
        label: 'New table',
        isNew: true,
      };
    }

    addTab(database, schemaId, newTab);
  }
</script>

<aside>
  <nav>
    <Tree data={tree} idKey="treeId" childKey="tables"
          search={true} {getLink} {expandedItems}
          bind:selectedItems={activeTable} on:nodeSelected={tableSelected}
          let:entry>
      <Icon data={faTable}/>
      <span>{entry.label}</span>

      <svelte:fragment slot="empty">
        No tables found
      </svelte:fragment>
    </Tree>
  </nav>
</aside>

<style global lang="scss">
  @import "LeftPane.scss";
</style>
