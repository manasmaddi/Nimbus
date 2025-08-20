import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  FileUp,
  LogIn,
  LogOut,
  CheckCircle,
  XCircle,
  Loader2,
  CloudUpload,
} from 'lucide-react';
import axios from 'axios';
import './App.css'; // Assuming you have a separate CSS file for the App component if needed
import './index.css'; // Make sure this is imported

const App = () => {
  const { isAuthenticated, loginWithRedirect, logout, getAccessTokenSilently } =
    useAuth0();
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleLogin = () => {
    loginWithRedirect();
  };

  const handleLogout = () => {
    logout({ returnTo: window.location.origin });
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadStatus('');
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadStatus('No file selected.');
      return;
    }

    if (!isAuthenticated) {
      setUploadStatus('You must be logged in to upload a file.');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading...');

    try {
      // Get the access token to send to the backend
      const accessToken = await getAccessTokenSilently({
        audience: process.env.REACT_APP_AUTH0_API_IDENTIFIER,
      });

      const formData = new FormData();
      formData.append('file', file);

      // Make the API call to your Flask backend
      const response = await axios.post(
        `${process.env.REACT_APP_API_BASE_URL}/api/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${accessToken}`, // Send the access token
          },
        }
      );

      setUploadStatus(response.data.message || 'Upload successful!');
    } catch (error) {
      console.error('File upload failed:', error);
      setUploadStatus(
        `Upload failed: ${error.response?.data?.message || error.message}`
      );
    } finally {
      setIsUploading(false);
    }
  };

  const getStatusClasses = () => {
    if (uploadStatus.includes('failed') || uploadStatus.includes('No file selected')) {
      return 'status-message red';
    } else if (uploadStatus.includes('successful')) {
      return 'status-message green';
    } else {
      return 'hidden';
    }
  };

  const getStatusIcon = () => {
    if (uploadStatus.includes('successful')) {
      return <CheckCircle className="mr-3" size={20} />;
    } else {
      return <XCircle className="mr-3" size={20} />;
    }
  };

  return (
    <div className="app-container">
      <div className="card">
        <h1 style={{fontSize: '1.875rem', fontWeight: 'bold', textAlign: 'center', color: '#1f2937', marginBottom: '1.5rem'}}>
          File Upload Portal
        </h1>

        <div style={{marginBottom: '1.5rem', display: 'flex', justifyContent: 'center'}}>
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="auth-button sign-out-button"
            >
              <LogOut className="mr-2" size={20} />
              Sign Out
            </button>
          ) : (
            <button
              onClick={handleLogin}
              className="auth-button sign-in-button"
            >
              <LogIn className="mr-2" size={20} />
              Sign In with Auth0
            </button>
          )}
        </div>

        {isAuthenticated && (
          <div style={{marginTop: '2rem'}}>
            <h2 style={{fontSize: '1.25rem', fontWeight: '600', color: '#374151', marginBottom: '1rem', textAlign: 'center'}}>
              Upload a File
            </h2>
            <form onSubmit={handleFileUpload} style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
              <label htmlFor="file-input" style={{display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151'}}>
                Choose a file:
              </label>
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%'}}>
                <label
                  htmlFor="file-input"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '100%',
                    height: '12rem',
                    border: '2px dashed #d1d5db',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    backgroundColor: '#f9fafb',
                    transition: 'background-color 0.3s',
                  }}
                >
                  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingTop: '1.25rem', paddingBottom: '1.5rem'}}>
                    <CloudUpload style={{width: '2.5rem', height: '2.5rem', marginBottom: '0.75rem', color: '#9ca3af'}} />
                    <p style={{marginBottom: '0.5rem', fontSize: '0.875rem', color: '#6b7280'}}>
                      <span style={{fontWeight: '600'}}>Click to upload</span> or
                      drag and drop
                    </p>
                    {file ? (
                      <p style={{fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem'}}>
                        Selected: {file.name}
                      </p>
                    ) : (
                      <p style={{fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem'}}>
                        Any file type is acceptable
                      </p>
                    )}
                  </div>
                  <input
                    id="file-input"
                    type="file"
                    style={{display: 'none'}}
                    onChange={handleFileChange}
                  />
                </label>
              </div>

              <button
                type="submit"
                disabled={!file || isUploading}
                className="upload-button"
                style={{width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.75rem 1.5rem', fontWeight: '600', color: '#fff', borderRadius: '9999px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="spinner" style={{marginRight: '0.5rem'}} size={20} />
                    Uploading...
                  </>
                ) : (
                  <>
                    <FileUp style={{marginRight: '0.5rem'}} size={20} />
                    Upload File
                  </>
                )}
              </button>
            </form>

            {uploadStatus && (
              <div
                className={getStatusClasses()}
              >
                {uploadStatus.includes('successful') ||
                uploadStatus.includes('No file selected') ? (
                  getStatusIcon()
                ) : (
                  getStatusIcon()
                )}
                {uploadStatus}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
