package com.farmintel.mobile

import android.app.AlertDialog
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Environment
import android.widget.ProgressBar
import android.widget.TextView
import androidx.core.content.FileProvider
import java.io.File

/**
 * FarmIntel Android - Model Download Manager
 * Handles downloading and managing the TinyLlama model
 */
class ModelDownloadManager(private val context: Context) {
    
    companion object {
        private const val MODEL_NAME = "tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf"
        private const val MODEL_SIZE = 400 * 1024 * 1024L // 400MB
        private const val MODEL_URL = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf"
        private const val PREFS_NAME = "FarmIntelPrefs"
        private const val KEY_MODEL_DOWNLOADED = "model_downloaded"
        private const val DOWNLOAD_ID_KEY = "model_download_id"
    }
    
    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val downloadManager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
    
    /**
     * Check if model is already downloaded
     */
    fun isModelDownloaded(): Boolean {
        val modelFile = getModelFile()
        
        if (!modelFile.exists()) {
            return false
        }
        
        // Verify file size (allow 10% variance)
        val fileSize = modelFile.length()
        if (fileSize < MODEL_SIZE * 0.9) {
            return false
        }
        
        return prefs.getBoolean(KEY_MODEL_DOWNLOADED, false)
    }
    
    /**
     * Get the model file path
     */
    fun getModelFile(): File {
        val modelsDir = File(context.getExternalFilesDir(null), "models")
        modelsDir.mkdirs()
        return File(modelsDir, MODEL_NAME)
    }
    
    /**
     * Show download dialog
     */
    fun showDownloadDialog(onDownload: () -> Unit, onSkip: () -> Unit) {
        AlertDialog.Builder(context)
            .setTitle("📥 Download Offline Model")
            .setMessage(
                "FarmIntel can work offline using a local AI model.\n\n" +
                "Model: TinyLlama 1.1B\n" +
                "Size: ~400 MB\n" +
                "Storage Required: 1 GB free space\n\n" +
                "✨ Benefits:\n" +
                "✓ Works completely offline\n" +
                "✓ Faster response times\n" +
                "✓ No internet required\n" +
                "✓ Privacy - data stays local"
            )
            .setPositiveButton("Download Model") { _, _ ->
                onDownload()
            }
            .setNegativeButton("Skip for Now") { _, _ ->
                onSkip()
            }
            .setCancelable(false)
            .show()
    }
    
    /**
     * Start downloading the model
     */
    fun startDownload(onProgress: (current: Long, total: Long) -> Unit, onComplete: () -> Unit, onError: (String) -> Unit) {
        try {
            // Check available storage
            val availableSpace = getAvailableStorage()
            if (availableSpace < MODEL_SIZE * 1.5) {
                onError("Not enough storage space. Need at least 1.5 GB free.")
                return
            }
            
            // Create request
            val request = DownloadManager.Request(Uri.parse(MODEL_URL))
                .setTitle("Downloading FarmIntel Model")
                .setDescription("TinyLlama 1.1B")
                .setDestinationUri(Uri.fromFile(getModelFile()))
                .setAllowedNetworkTypes(DownloadManager.Request.NETWORK_WIFI or DownloadManager.Request.NETWORK_MOBILE)
                .setAllowedOverRoaming(false)
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            
            // Start download
            val downloadId = downloadManager.enqueue(request)
            prefs.edit().putLong(DOWNLOAD_ID_KEY, downloadId).apply()
            
            // Monitor download progress
            monitorDownload(downloadId, onProgress, onComplete, onError)
            
        } catch (e: Exception) {
            onError("Failed to start download: ${e.message}")
        }
    }
    
    /**
     * Monitor download progress
     */
    private fun monitorDownload(
        downloadId: Long,
        onProgress: (current: Long, total: Long) -> Unit,
        onComplete: () -> Unit,
        onError: (String) -> Unit
    ) {
        Thread {
            var isDownloading = true
            var lastProgress = 0L
            
            while (isDownloading) {
                try {
                    val query = DownloadManager.Query().setFilterById(downloadId)
                    val cursor = downloadManager.query(query)
                    
                    if (cursor.moveToFirst()) {
                        val status = cursor.getInt(cursor.getColumnIndex(DownloadManager.COLUMN_STATUS))
                        val downloaded = cursor.getLong(cursor.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
                        val total = cursor.getLong(cursor.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))
                        
                        if (downloaded != lastProgress) {
                            onProgress(downloaded, total)
                            lastProgress = downloaded
                        }
                        
                        when (status) {
                            DownloadManager.STATUS_SUCCESSFUL -> {
                                isDownloading = false
                                prefs.edit().putBoolean(KEY_MODEL_DOWNLOADED, true).apply()
                                onComplete()
                            }
                            DownloadManager.STATUS_FAILED -> {
                                isDownloading = false
                                val reason = cursor.getInt(cursor.getColumnIndex(DownloadManager.COLUMN_REASON))
                                onError("Download failed with reason code: $reason")
                            }
                            DownloadManager.STATUS_PAUSED -> {
                                // Continue waiting
                            }
                        }
                    }
                    
                    cursor.close()
                    Thread.sleep(500)
                    
                } catch (e: Exception) {
                    isDownloading = false
                    onError("Error monitoring download: ${e.message}")
                }
            }
        }.start()
    }
    
    /**
     * Get available storage space
     */
    private fun getAvailableStorage(): Long {
        val stat = android.os.StatFs(Environment.getExternalStorageDirectory().path)
        return stat.availableBlocksLong * stat.blockSizeLong
    }
    
    /**
     * Cancel download
     */
    fun cancelDownload() {
        val downloadId = prefs.getLong(DOWNLOAD_ID_KEY, -1)
        if (downloadId != -1L) {
            downloadManager.remove(downloadId)
            prefs.edit().remove(DOWNLOAD_ID_KEY).apply()
        }
    }
}

/**
 * Download progress dialog for Android
 */
class ModelDownloadDialog(
    private val context: Context,
    private val manager: ModelDownloadManager
) {
    
    private var dialog: AlertDialog? = null
    private var progressBar: ProgressBar? = null
    private var statusText: TextView? = null
    
    fun show(onComplete: () -> Unit) {
        val builder = AlertDialog.Builder(context)
        builder.setTitle("📥 Downloading Model")
        builder.setCancelable(false)
        
        // Create custom view with progress
        val view = android.widget.LinearLayout(context).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(20, 20, 20, 20)
            
            // Progress bar
            progressBar = ProgressBar(context, null, android.R.attr.progressBarStyleHorizontal).apply {
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                    android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
                )
                max = 100
                progress = 0
            }
            addView(progressBar)
            
            // Status text
            statusText = TextView(context).apply {
                layoutParams = android.widget.LinearLayout.LayoutParams(
                    android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                    android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    topMargin = 16
                }
                text = "0 MB / 400 MB (0%)"
                textSize = 14f
            }
            addView(statusText)
        }
        
        builder.setView(view)
        builder.setNegativeButton("Cancel") { _, _ ->
            manager.cancelDownload()
        }
        
        dialog = builder.create()
        dialog?.show()
        
        // Start download
        manager.startDownload(
            onProgress = { current, total ->
                val percent = (current * 100 / total).toInt()
                val mb = current / (1024 * 1024)
                val totalMb = total / (1024 * 1024)
                
                progressBar?.progress = percent
                statusText?.text = "$mb MB / $totalMb MB ($percent%)"
            },
            onComplete = {
                dialog?.dismiss()
                onComplete()
            },
            onError = { error ->
                dialog?.dismiss()
                AlertDialog.Builder(context)
                    .setTitle("Download Failed")
                    .setMessage(error)
                    .setPositiveButton("OK", null)
                    .show()
            }
        )
    }
}
