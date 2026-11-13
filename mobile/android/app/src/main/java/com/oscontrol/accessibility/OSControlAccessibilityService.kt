package com.oscontrol.accessibility

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.util.Log

class OSControlAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "OSControlA11y"
        var instance: OSControlAccessibilityService? = null
            private set
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "OS-Control Accessibility Service Connected")

        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPES_ALL_MASK
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
            notificationTimeout = 100
        }
        serviceInfo = info
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        Log.d(TAG, "Event: ${event.eventType} from ${event.packageName}")
    }

    override fun onInterrupt() {
        Log.w(TAG, "OS-Control Service Interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
        Log.i(TAG, "OS-Control Service Destroyed")
    }

    /**
     * Traverses the active window tree and serializes nodes into a map
     */
    fun dumpActiveWindowTree(): List<Map<String, Any?>> {
        val rootNode = rootInActiveWindow ?: return emptyList()
        val elements = mutableListOf<Map<String, Any?>>()
        traverseNode(rootNode, elements)
        return elements
    }

    private fun traverseNode(node: AccessibilityNodeInfo, list: MutableList<Map<String, Any?>>) {
        val map = mapOf(
            "text" to node.text?.toString(),
            "content_desc" to node.contentDescription?.toString(),
            "view_id" to node.viewIdResourceName,
            "class_name" to node.className?.toString(),
            "is_clickable" to node.isClickable,
            "is_enabled" to node.isEnabled,
            "is_focused" to node.isFocused
        )
        list.add(map)

        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            traverseNode(child, list)
        }
    }
}

