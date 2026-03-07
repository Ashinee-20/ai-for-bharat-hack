package com.farmintel.mobile

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp
import androidx.navigation.ui.setupActionBarWithNavController
import com.farmintel.mobile.databinding.ActivityMainBinding

/**
 * FarmIntel Android - Main Activity
 * Entry point with model download on first run
 */
class MainActivity : AppCompatActivity() {
    
    private lateinit var appBarConfiguration: AppBarConfiguration
    private lateinit var binding: ActivityMainBinding
    private lateinit var modelManager: ModelDownloadManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setSupportActionBar(binding.toolbar)
        
        val navController = findNavController(R.id.nav_host_fragment_content_main)
        appBarConfiguration = AppBarConfiguration(navController.graph)
        setupActionBarWithNavController(navController, appBarConfiguration)
        
        // Initialize model manager
        modelManager = ModelDownloadManager(this)
        
        // Check if model needs to be downloaded
        checkAndDownloadModel()
    }
    
    /**
     * Check if model is downloaded, show dialog if needed
     */
    private fun checkAndDownloadModel() {
        if (!modelManager.isModelDownloaded()) {
            showModelDownloadDialog()
        }
    }
    
    /**
     * Show model download dialog
     */
    private fun showModelDownloadDialog() {
        modelManager.showDownloadDialog(
            onDownload = {
                val downloadDialog = ModelDownloadDialog(this, modelManager)
                downloadDialog.show {
                    // Download complete
                    showDownloadCompleteMessage()
                }
            },
            onSkip = {
                // User skipped download
                showSkipMessage()
            }
        )
    }
    
    /**
     * Show download complete message
     */
    private fun showDownloadCompleteMessage() {
        android.app.AlertDialog.Builder(this)
            .setTitle("✓ Success")
            .setMessage("Model downloaded successfully!\nYou can now use FarmIntel offline.")
            .setPositiveButton("OK", null)
            .show()
    }
    
    /**
     * Show skip message
     */
    private fun showSkipMessage() {
        android.app.AlertDialog.Builder(this)
            .setTitle("ℹ️ Offline Mode Limited")
            .setMessage(
                "You skipped the model download.\n\n" +
                "FarmIntel will work in online mode only.\n" +
                "You can download the model later from Settings."
            )
            .setPositiveButton("OK", null)
            .show()
    }
    
    override fun onSupportNavigateUp(): Boolean {
        val navController = findNavController(R.id.nav_host_fragment_content_main)
        return navController.navigateUp(appBarConfiguration) || super.onSupportNavigateUp()
    }
}
