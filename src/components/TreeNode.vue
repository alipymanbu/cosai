<template>
  <div class="tree-node">
    <div 
      class="node-header" 
      :class="{ 'is-folder': node.type === 'folder', 'is-file': node.type === 'file' }"
      :style="{ paddingLeft: `${8 + depth * 16}px` }"
      @click="handleClick"
      @contextmenu="handleContextMenu"
    >
      <span class="arrow" v-if="node.type === 'folder'">
        <span class="arrow-icon" :class="{ expanded: isExpanded }">▶</span>
      </span>
      <span class="arrow" v-else></span>
      
      <span class="icon" :class="node.type">
        <Folder v-if="node.type === 'folder'" class="folder-icon" />
        <Document v-else class="file-icon" />
      </span>
      
      <span class="name">{{ node.label }}</span>
    </div>
    
    <div v-if="node.type === 'folder' && isExpanded" class="node-children">
      <TreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :expanded-nodes="expandedNodes"
        @toggle="$emit('toggle', $event)"
        @select="$emit('select', $event)"
        @contextmenu="handleChildContextMenu"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Folder, Document } from '@element-plus/icons-vue'

interface TreeNodeData {
  id: string
  label: string
  type: 'folder' | 'file'
  children?: TreeNodeData[]
  filePath?: string
}

const props = defineProps<{
  node: TreeNodeData
  depth: number
  expandedNodes: Set<string>
}>()

const emit = defineEmits<{
  toggle: [nodeId: string]
  select: [node: TreeNodeData]
  contextmenu: [event: MouseEvent, node: TreeNodeData]
}>()

const isExpanded = computed(() => {
  return props.expandedNodes.has(props.node.id)
})

const handleClick = () => {
  if (props.node.type === 'folder') {
    emit('toggle', props.node.id)
  } else {
    emit('select', props.node)
  }
}

const handleContextMenu = (e: MouseEvent) => {
  emit('contextmenu', e, props.node)
}

const handleChildContextMenu = (e: MouseEvent, node: TreeNodeData) => {
  emit('contextmenu', e, node)
}
</script>

<style scoped lang="scss">
.tree-node {
  .node-header {
    display: flex;
    align-items: center;
    padding: 4px 8px;
    cursor: pointer;
    user-select: none;
    transition: background 0.1s ease;
    border-radius: 4px;
    margin: 0 4px;
    
    &:hover {
      background: #2a2d2e;
    }
    
    &.is-file:hover {
      background: #094771;
      
      .name {
        color: #ffffff;
      }
    }
    
    .arrow {
      width: 16px;
      height: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-right: 2px;
      
      .arrow-icon {
        font-size: 10px;
        color: #858585;
        transition: transform 0.15s ease;
        display: inline-block;
        
        &.expanded {
          transform: rotate(90deg);
        }
      }
    }
    
    .icon {
      display: flex;
      align-items: center;
      margin-right: 6px;
      flex-shrink: 0;
      
      .folder-icon {
        width: 16px;
        height: 16px;
        color: #dcb67a;
      }
      
      .file-icon {
        width: 16px;
        height: 16px;
        color: #cccccc;
      }
    }
    
    .name {
      color: #cccccc;
      font-size: 13px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  
  .node-children {
    overflow: hidden;
  }
}
</style>
